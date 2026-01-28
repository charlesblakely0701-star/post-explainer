"""Test runner for the evaluation harness."""

import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import calculate_all_metrics


async def run_single_test(
    test_case: Dict[str, Any],
    explainer,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run a single test case through the explainer.
    
    Args:
        test_case: The test case to run
        explainer: PostExplainer instance
        verbose: Whether to print progress
        
    Returns:
        Test result dict
    """
    test_id = test_case["id"]
    post_text = test_case["post_text"]
    
    if verbose:
        print(f"  Running test: {test_id}")
        print(f"  Post: {post_text[:60]}...")
    
    start_time = time.time()
    
    try:
        # Run the explainer
        result = await explainer.explain(post_text, use_cache=False)
        
        elapsed_time = time.time() - start_time
        
        # Calculate metrics
        explanation_text = '\n'.join(f"• {b}" for b in result.bullets)
        metrics = calculate_all_metrics(
            explanation_text,
            test_case,
            len(result.sources)
        )
        
        return {
            "test_id": test_id,
            "status": "passed" if metrics["pass"] else "failed",
            "post_text": post_text,
            "generated_bullets": result.bullets,
            "sources": [s.model_dump() for s in result.sources],
            "metrics": metrics,
            "elapsed_time": elapsed_time,
            "error": None
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "test_id": test_id,
            "status": "error",
            "post_text": post_text,
            "generated_bullets": [],
            "sources": [],
            "metrics": None,
            "elapsed_time": elapsed_time,
            "error": str(e)
        }


async def run_all_tests(
    test_cases: List[Dict[str, Any]],
    explainer,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run all test cases.
    
    Args:
        test_cases: List of test cases
        explainer: PostExplainer instance
        verbose: Whether to print progress
        
    Returns:
        Full evaluation results
    """
    results = []
    total_start = time.time()
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Running {len(test_cases)} test cases")
        print(f"{'='*60}\n")
    
    for i, test_case in enumerate(test_cases, 1):
        if verbose:
            print(f"[{i}/{len(test_cases)}] {test_case['id']}")
        
        result = await run_single_test(test_case, explainer, verbose)
        results.append(result)
        
        if verbose:
            # Use ASCII-safe symbols for Windows compatibility
            status_symbol = "[PASS]" if result["status"] == "passed" else "[FAIL]" if result["status"] == "failed" else "[ERR]"
            score = result["metrics"]["overall_score"] if result["metrics"] else 0
            print(f"  {status_symbol} Score: {score:.2f} | Time: {result['elapsed_time']:.2f}s\n")
    
    total_time = time.time() - total_start
    
    # Calculate summary statistics
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    errors = sum(1 for r in results if r["status"] == "error")
    
    scores = [r["metrics"]["overall_score"] for r in results if r["metrics"]]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    times = [r["elapsed_time"] for r in results]
    avg_time = sum(times) / len(times) if times else 0
    
    summary = {
        "total_tests": len(test_cases),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": passed / len(test_cases) if test_cases else 0,
        "average_score": avg_score,
        "average_time": avg_time,
        "total_time": total_time,
    }
    
    if verbose:
        print(f"{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {summary['total_tests']} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
        print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
        print(f"Average Score: {avg_score:.3f}")
        print(f"Average Time: {avg_time:.2f}s")
        print(f"Total Time: {total_time:.2f}s")
        print(f"{'='*60}\n")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "results": results
    }


def load_test_cases(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load test cases from JSON file.
    
    Args:
        path: Path to test cases file. Defaults to evaluation/test_cases.json
        
    Returns:
        List of test case dicts
    """
    if path is None:
        path = Path(__file__).parent / "test_cases.json"
    
    with open(path) as f:
        return json.load(f)


def save_results(results: Dict[str, Any], path: Optional[str] = None) -> str:
    """
    Save evaluation results to JSON file.
    
    Args:
        results: Evaluation results dict
        path: Output path. Defaults to evaluation/results/results_<timestamp>.json
        
    Returns:
        Path to saved file
    """
    if path is None:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = results_dir / f"results_{timestamp}.json"
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return str(path)

