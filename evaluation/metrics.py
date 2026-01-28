"""Evaluation metrics for assessing explanation quality."""

import re
from typing import List, Dict, Any
import numpy as np

# Lazy import for sentence transformers (optional dependency)
_model = None


def get_embedding_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            print("Warning: sentence-transformers not installed. Semantic similarity will be skipped.")
            return None
    return _model


def calculate_keyword_coverage(
    explanation: str,
    expected_keywords: List[str]
) -> Dict[str, Any]:
    """
    Calculate what percentage of expected keywords appear in the explanation.
    
    Args:
        explanation: The generated explanation text
        expected_keywords: List of keywords that should appear
        
    Returns:
        Dict with coverage score and details
    """
    explanation_lower = explanation.lower()
    found_keywords = []
    missing_keywords = []
    
    for keyword in expected_keywords:
        if keyword.lower() in explanation_lower:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    coverage = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
    
    return {
        "score": coverage,
        "found": found_keywords,
        "missing": missing_keywords,
        "total_expected": len(expected_keywords),
        "total_found": len(found_keywords),
    }


def calculate_topic_coverage(
    explanation: str,
    expected_topics: List[str]
) -> Dict[str, Any]:
    """
    Calculate what percentage of expected topics are addressed.
    Uses fuzzy matching for topic detection.
    
    Args:
        explanation: The generated explanation text
        expected_topics: List of topics that should be covered
        
    Returns:
        Dict with coverage score and details
    """
    explanation_lower = explanation.lower()
    found_topics = []
    missing_topics = []
    
    for topic in expected_topics:
        # Check for the topic or related words
        topic_words = topic.lower().split()
        
        # Consider topic found if any significant word appears
        if any(word in explanation_lower for word in topic_words if len(word) > 3):
            found_topics.append(topic)
        else:
            missing_topics.append(topic)
    
    coverage = len(found_topics) / len(expected_topics) if expected_topics else 0
    
    return {
        "score": coverage,
        "found": found_topics,
        "missing": missing_topics,
        "total_expected": len(expected_topics),
        "total_found": len(found_topics),
    }


def calculate_semantic_similarity(
    generated: str,
    reference: str
) -> Dict[str, Any]:
    """
    Calculate semantic similarity between generated and reference explanations.
    Uses sentence embeddings for comparison.
    
    Args:
        generated: The generated explanation
        reference: The reference/expected explanation
        
    Returns:
        Dict with similarity score
    """
    model = get_embedding_model()
    
    if model is None:
        return {
            "score": None,
            "error": "sentence-transformers not available"
        }
    
    try:
        # Get embeddings
        gen_embedding = model.encode(generated, convert_to_numpy=True)
        ref_embedding = model.encode(reference, convert_to_numpy=True)
        
        # Calculate cosine similarity
        similarity = float(np.dot(gen_embedding, ref_embedding) / (
            np.linalg.norm(gen_embedding) * np.linalg.norm(ref_embedding)
        ))
        
        return {
            "score": similarity,
            "interpretation": interpret_similarity(similarity)
        }
    except Exception as e:
        return {
            "score": None,
            "error": str(e)
        }


def interpret_similarity(score: float) -> str:
    """Interpret a similarity score."""
    if score >= 0.8:
        return "excellent"
    elif score >= 0.6:
        return "good"
    elif score >= 0.4:
        return "fair"
    else:
        return "poor"


def calculate_citation_quality(
    explanation: str,
    num_sources: int
) -> Dict[str, Any]:
    """
    Evaluate the quality of citations in the explanation.
    
    Args:
        explanation: The generated explanation with citations
        num_sources: Number of available sources
        
    Returns:
        Dict with citation quality metrics
    """
    # Find all citation references [1], [2], etc.
    citations = re.findall(r'\[(\d+)\]', explanation)
    unique_citations = set(int(c) for c in citations)
    
    # Check if citations are valid (within source range)
    valid_citations = [c for c in unique_citations if 1 <= c <= num_sources]
    invalid_citations = [c for c in unique_citations if c > num_sources]
    
    # Calculate metrics
    has_citations = len(citations) > 0
    citation_diversity = len(unique_citations) / max(num_sources, 1)
    
    return {
        "has_citations": has_citations,
        "total_citations": len(citations),
        "unique_citations": len(unique_citations),
        "valid_citations": len(valid_citations),
        "invalid_citations": invalid_citations,
        "citation_diversity": min(citation_diversity, 1.0),
        "score": 1.0 if has_citations and not invalid_citations else 0.5 if has_citations else 0.0
    }


def calculate_format_quality(explanation: str) -> Dict[str, Any]:
    """
    Evaluate the format quality of the explanation.
    
    Args:
        explanation: The generated explanation
        
    Returns:
        Dict with format quality metrics
    """
    lines = [l.strip() for l in explanation.strip().split('\n') if l.strip()]
    
    # Check for bullet format
    bullet_lines = [l for l in lines if l.startswith(('•', '-', '*', '1', '2', '3', '4', '5'))]
    
    # Calculate metrics
    num_bullets = len(bullet_lines)
    has_proper_format = 3 <= num_bullets <= 5
    
    # Average bullet length
    bullet_lengths = [len(l) for l in bullet_lines]
    avg_length = sum(bullet_lengths) / len(bullet_lengths) if bullet_lengths else 0
    
    # Check for reasonable length (not too short, not too long)
    good_length = 50 <= avg_length <= 300
    
    return {
        "num_bullets": num_bullets,
        "has_proper_format": has_proper_format,
        "avg_bullet_length": avg_length,
        "good_length": good_length,
        "score": 1.0 if has_proper_format and good_length else 0.5 if has_proper_format else 0.0
    }


def calculate_all_metrics(
    explanation: str,
    test_case: Dict[str, Any],
    num_sources: int
) -> Dict[str, Any]:
    """
    Calculate all metrics for an explanation.
    
    Args:
        explanation: The generated explanation
        test_case: The test case with expected values
        num_sources: Number of sources returned
        
    Returns:
        Dict with all metric results
    """
    # Join bullets if it's a list
    if isinstance(explanation, list):
        explanation = '\n'.join(f"• {b}" for b in explanation)
    
    keyword_metrics = calculate_keyword_coverage(
        explanation,
        test_case.get("expected_keywords", [])
    )
    
    topic_metrics = calculate_topic_coverage(
        explanation,
        test_case.get("expected_topics", [])
    )
    
    semantic_metrics = calculate_semantic_similarity(
        explanation,
        test_case.get("reference_explanation", "")
    )
    
    citation_metrics = calculate_citation_quality(explanation, num_sources)
    format_metrics = calculate_format_quality(explanation)
    
    # Calculate overall score
    scores = [
        keyword_metrics["score"] * 0.25,
        topic_metrics["score"] * 0.25,
        (semantic_metrics.get("score") or 0) * 0.25,
        citation_metrics["score"] * 0.15,
        format_metrics["score"] * 0.10,
    ]
    overall_score = sum(scores)
    
    return {
        "overall_score": overall_score,
        "keyword_coverage": keyword_metrics,
        "topic_coverage": topic_metrics,
        "semantic_similarity": semantic_metrics,
        "citation_quality": citation_metrics,
        "format_quality": format_metrics,
        "pass": overall_score >= 0.5,  # 50% threshold
    }

