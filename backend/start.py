from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from uuid import uuid4
from langchain_core.messages import HumanMessage
from graph import graph
import json
import asyncio

router = APIRouter()

@router.get("/start_interview")
async def start_interview(
    name: str = Query(...),
    interview_type: str = Query(...),
    user_id: str = Query(...),
    max_questions: int = Query(3)  
):
    checkpoint_id = str(uuid4())
    session_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": checkpoint_id
        }
    }

    initial_state = {
        "name": name,
        "interview_type": interview_type,
        "user_id": user_id,
        "messages": [],
        "answers": [],
        "question_count": 0,
        "max_questions": max_questions,
        "session_id": session_id,
        "score": None,
        "previous_session": None
    }

    async def event_stream():
        yield f"data: {{\"type\": \"checkpoint\", \"checkpoint_id\": \"{checkpoint_id}\"}}\n\n"
        yield f"data: {{\"type\": \"session\", \"session_id\": \"{session_id}\"}}\n\n"

        async for event in graph.astream_events(
            input=initial_state,
            config=config,
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content.replace("\n", "\\n").replace('"', '\\"')
                yield f"data: {{\"type\": \"content\", \"content\": \"{content}\"}}\n\n"
        
        yield f"data: {{\"type\": \"end\"}}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")