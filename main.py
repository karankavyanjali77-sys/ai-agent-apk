"""
Cloud Run HTTP server for the Text Intelligence ADK Agent.
Exposes a /run endpoint that accepts POST requests and streams agent responses.
"""

import os
import json
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import root_agent

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App Setup ---
app = FastAPI(
    title="Text Intelligence Agent",
    description="ADK-powered text summarization and sentiment analysis agent on Cloud Run.",
    version="1.0.0",
)

# ADK session service (in-memory for stateless Cloud Run)
session_service = InMemorySessionService()

APP_NAME = "text_intelligence_agent"
USER_ID = "cloud_run_user"


# --- Request / Response Models ---

class RunRequest(BaseModel):
    message: str
    session_id: str = "default"


class RunResponse(BaseModel):
    session_id: str
    response: str
    status: str = "success"


# --- Endpoints ---

@app.get("/", summary="Health check")
async def root():
    return {
        "service": "Text Intelligence Agent",
        "status": "running",
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        "endpoints": {
            "POST /run": "Send a message to the agent",
            "GET /health": "Health check",
        },
    }


@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse, summary="Run the agent")
async def run_agent(req: RunRequest):
    """
    Send a message to the Text Intelligence Agent.

    Example body:
    ```json
    {
      "message": "Summarize this in bullet points: The Eiffel Tower was built ...",
      "session_id": "user-abc-123"
    }
    ```
    """
    session_id = req.session_id

    try:
        # Create or retrieve session
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        if session is None:
            session = await session_service.create_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=session_id
            )

        # Build runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        # Package user message
        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=req.message)],
        )

        # Collect final text response
        final_response = ""
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = "".join(
                        p.text for p in event.content.parts if hasattr(p, "text")
                    )

        if not final_response:
            raise HTTPException(status_code=500, detail="Agent returned no response.")

        logger.info(f"Session={session_id} | Response length={len(final_response)}")
        return RunResponse(session_id=session_id, response=final_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
