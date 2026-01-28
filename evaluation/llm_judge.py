"""LLM-as-Judge evaluation for explanation quality."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

JUDGE_PROMPT = """You are an expert evaluator assessing the quality of AI-generated explanations for social media posts.

ORIGINAL POST:
"{post_text}"

GENERATED EXPLANATION:
{explanation}

REFERENCE EXPLANATION (for context, not exact match required):
{reference}

Please evaluate the generated explanation on these criteria (1-5 scale):

1. **Accuracy** (1-5): Is the information factually correct based on what you know? Are there any hallucinations or false claims?

2. **Relevance** (1-5): Does the explanation actually help understand the post? Does it address the key references and context needed?

3. **Completeness** (1-5): Does it cover the main points? Is anything important missing?

4. **Clarity** (1-5): Is the explanation clear and easy to understand? Is it well-structured?

5. **Citation Quality** (1-5): Are sources cited appropriately? Do citations support the claims made?

Respond in this exact JSON format:
{{
    "accuracy": <1-5>,
    "relevance": <1-5>,
    "completeness": <1-5>,
    "clarity": <1-5>,
    "citation_quality": <1-5>,
    "overall": <1-5>,
    "reasoning": "<brief explanation of scores>"
}}
"""


class LLMJudge:
    """Use LLM to evaluate explanation quality."""
    
    def __init__(self, api_key: Optional[str] = None):
        from openai import AsyncOpenAI
        
        if api_key is None:
            from config import get_settings
            settings = get_settings()
            api_key = settings.openai_api_key
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
    
    async def evaluate(
        self,
        post_text: str,
        explanation: str,
        reference: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate an explanation using LLM-as-judge.
        
        Args:
            post_text: Original post
            explanation: Generated explanation to evaluate
            reference: Reference explanation (optional)
            
        Returns:
            Dict with scores and reasoning
        """
        prompt = JUDGE_PROMPT.format(
            post_text=post_text,
            explanation=explanation,
            reference=reference or "Not provided"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent evaluation
            )
            
            content = response.choices[0].message.content or "{}"
            
            # Extract JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            # Calculate weighted overall if not provided
            if "overall" not in result:
                weights = {
                    "accuracy": 0.3,
                    "relevance": 0.25,
                    "completeness": 0.2,
                    "clarity": 0.15,
                    "citation_quality": 0.1
                }
                result["overall"] = sum(
                    result.get(k, 3) * w 
                    for k, w in weights.items()
                )
            
            return {
                "scores": result,
                "pass": result.get("overall", 0) >= 3.5,
                "error": None
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse judge response: {e}")
            return {
                "scores": {},
                "pass": False,
                "error": f"JSON parse error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Judge evaluation error: {e}")
            return {
                "scores": {},
                "pass": False,
                "error": str(e)
            }
    
    async def evaluate_batch(
        self,
        evaluations: list[tuple[str, str, str]]
    ) -> list[Dict[str, Any]]:
        """
        Evaluate multiple explanations in parallel.
        
        Args:
            evaluations: List of (post_text, explanation, reference) tuples
            
        Returns:
            List of evaluation results
        """
        tasks = [
            self.evaluate(post, explanation, reference)
            for post, explanation, reference in evaluations
        ]
        return await asyncio.gather(*tasks)


async def run_llm_judge_evaluation(
    results_file: str,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run LLM-as-judge evaluation on existing results.
    
    Args:
        results_file: Path to results JSON from runner
        output_file: Optional path to save enriched results
        
    Returns:
        Summary of LLM judge evaluations
    """
    from evaluation.runner import load_test_cases
    
    # Load results
    with open(results_file) as f:
        results = json.load(f)
    
    # Load test cases for reference explanations
    test_cases = {tc["id"]: tc for tc in load_test_cases()}
    
    # Initialize judge
    judge = LLMJudge()
    
    # Evaluate each result
    enriched_results = []
    for result in results["results"]:
        if result["status"] == "error":
            enriched_results.append(result)
            continue
        
        test_case = test_cases.get(result["test_id"], {})
        explanation = "\n".join(f"• {b}" for b in result["generated_bullets"])
        reference = test_case.get("reference_explanation", "")
        
        judge_result = await judge.evaluate(
            result["post_text"],
            explanation,
            reference
        )
        
        result["llm_judge"] = judge_result
        enriched_results.append(result)
    
    # Calculate summary
    judge_scores = [
        r["llm_judge"]["scores"].get("overall", 0)
        for r in enriched_results
        if r.get("llm_judge", {}).get("scores")
    ]
    
    summary = {
        "total_evaluated": len(judge_scores),
        "average_score": sum(judge_scores) / len(judge_scores) if judge_scores else 0,
        "pass_rate": sum(1 for r in enriched_results if r.get("llm_judge", {}).get("pass", False)) / len(enriched_results) if enriched_results else 0,
    }
    
    # Save enriched results
    output = {
        "original_summary": results["summary"],
        "llm_judge_summary": summary,
        "results": enriched_results
    }
    
    if output_file:
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
    
    return output


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python llm_judge.py <results_file> [output_file]")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = asyncio.run(run_llm_judge_evaluation(results_file, output_file))
    
    print(f"\nLLM Judge Summary:")
    print(f"  Evaluated: {result['llm_judge_summary']['total_evaluated']}")
    print(f"  Average Score: {result['llm_judge_summary']['average_score']:.2f}/5")
    print(f"  Pass Rate: {result['llm_judge_summary']['pass_rate']*100:.1f}%")

