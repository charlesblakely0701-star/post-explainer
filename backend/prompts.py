"""Prompt templates for the LLM."""


EXPLANATION_PROMPT = """You are explaining a social media post to someone who is unfamiliar with its context or references.

ORIGINAL POST:
"{post_text}"

SEARCH RESULTS FOR CONTEXT:
{search_context}

INSTRUCTIONS:
1. Generate 3-5 bullet points explaining what this post is about
2. Each bullet should be concise (1-2 sentences max)
3. Focus on:
   - What is being referenced? (terms, people, events, memes)
   - Why does it matter or why is it interesting?
   - Key background context needed to understand the post
4. Add citation numbers [1], [2], etc. at the end of statements, referencing the sources above
5. Only include information that is supported by the search results
6. If search results don't provide enough context, acknowledge this honestly

RESPONSE FORMAT:
Return ONLY the bullet points in this exact format:
• [First explanation point] [1]
• [Second explanation point] [2]  
• [Third explanation point] [1][3]
(etc.)

Do NOT include any preamble, headers, or additional text. Start directly with the first bullet point."""


def build_explanation_prompt(post_text: str, search_results: list) -> str:
    """
    Build the full prompt for generating an explanation.
    
    Args:
        post_text: The original social media post
        search_results: List of SearchResult objects
        
    Returns:
        Formatted prompt string
    """
    # Format search results with numbered citations
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_parts.append(
            f"[{i}] {result.title}\n"
            f"    URL: {result.url}\n"
            f"    Content: {result.snippet}"
        )
    
    search_context = "\n\n".join(context_parts) if context_parts else "No relevant search results found."
    
    return EXPLANATION_PROMPT.format(
        post_text=post_text,
        search_context=search_context
    )

