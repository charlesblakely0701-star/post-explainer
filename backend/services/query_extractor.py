"""Query extraction from social media posts - no LLM needed."""

import re
from typing import List


def extract_search_queries(post_text: str) -> List[str]:
    """
    Extract search queries from a social media post.
    Uses simple heuristics - no LLM needed.
    
    Args:
        post_text: The original post text
        
    Returns:
        List of 1-3 search queries
    """
    queries = []
    
    # Clean the text
    text = post_text.strip()
    
    # Query 1: The full post (often works best for short posts)
    # Truncate if too long, search engines handle ~200 chars well
    if len(text) <= 200:
        queries.append(text)
    else:
        # Take first sentence or first 200 chars
        first_sentence = re.split(r'[.!?]', text)[0]
        if len(first_sentence) <= 200:
            queries.append(first_sentence)
        else:
            queries.append(text[:200])
    
    # Query 2: Extract quoted phrases (often key terms)
    quoted_phrases = re.findall(r'["\']([^"\']+)["\']', text)
    for phrase in quoted_phrases[:2]:  # Max 2 quoted phrases
        if len(phrase) > 3 and phrase not in queries:
            queries.append(phrase)
    
    # Query 3: Extract hashtags (without the #)
    hashtags = re.findall(r'#(\w+)', text)
    if hashtags:
        hashtag_query = ' '.join(hashtags[:3])  # Max 3 hashtags
        if hashtag_query not in queries:
            queries.append(hashtag_query)
    
    # Query 4: Extract capitalized phrases (proper nouns, names, techniques)
    # Match 2+ consecutive capitalized words
    cap_phrases = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
    for phrase in cap_phrases[:2]:
        if phrase not in queries and len(phrase) > 5:
            queries.append(phrase)
    
    # Query 5: Extract @mentions (usernames might be searchable)
    mentions = re.findall(r'@(\w+)', text)
    for mention in mentions[:1]:  # Max 1 mention
        if len(mention) > 3:
            queries.append(f"{mention} social media")
    
    # Deduplicate and limit
    seen = set()
    unique_queries = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower not in seen and len(q_lower) > 3:
            seen.add(q_lower)
            unique_queries.append(q)
    
    # Return max 3 queries
    return unique_queries[:3] if unique_queries else [text[:200]]

