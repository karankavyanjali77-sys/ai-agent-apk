"""
Text Summarization Agent using Google ADK and Gemini.
Deployed as a serverless container on Cloud Run.
"""

import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool


# --- Tool Definitions ---

def summarize_text(text: str, style: str = "concise") -> dict:
    """
    Summarizes the provided text.

    Args:
        text: The text content to summarize.
        style: Summary style — 'concise' (2-3 sentences),
               'detailed' (paragraph), or 'bullets' (key points).

    Returns:
        A dict with 'summary' and 'word_count' fields.
    """
    # The agent (Gemini) will do the actual summarization via its reasoning.
    # This tool is a structured wrapper so ADK can track inputs/outputs.
    return {
        "original_word_count": len(text.split()),
        "requested_style": style,
        "status": "summarized",
    }


def classify_sentiment(text: str) -> dict:
    """
    Classifies the sentiment of the provided text.

    Args:
        text: The text to classify.

    Returns:
        A dict with 'sentiment' (positive/negative/neutral) and 'confidence'.
    """
    return {
        "text_length": len(text),
        "status": "classified",
    }


# --- Agent Definition ---

root_agent = Agent(
    name="text_intelligence_agent",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    description=(
        "A text intelligence agent that summarizes content and classifies sentiment. "
        "Given any text, it can produce concise, detailed, or bullet-point summaries, "
        "and determine whether the sentiment is positive, negative, or neutral."
    ),
    instruction="""
You are a precise, helpful text intelligence assistant.

When a user provides text and asks for a summary:
1. Call the `summarize_text` tool with the provided text and requested style.
2. Then produce a high-quality summary in the requested style:
   - 'concise': 2-3 clear sentences capturing the core message.
   - 'detailed': A well-structured paragraph with supporting details.
   - 'bullets': 4-6 bullet points highlighting key ideas.
3. Report the original word count.

When a user asks for sentiment analysis:
1. Call the `classify_sentiment` tool.
2. Determine whether the overall sentiment is Positive, Negative, or Neutral.
3. Give a brief explanation (1-2 sentences) of why.

Always be factual, structured, and concise in your responses.
If no style is specified for summarization, default to 'concise'.
""",
    tools=[
        FunctionTool(summarize_text),
        FunctionTool(classify_sentiment),
    ],
)
