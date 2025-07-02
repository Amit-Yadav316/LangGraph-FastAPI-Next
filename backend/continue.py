from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessageChunk
from graph import graph

router = APIRouter()

def serialise_ai_message_chunk(chunk):
    if isinstance(chunk, AIMessageChunk):
        return chunk.content
    raise TypeError("Expected AIMessageChunk")

@router.get("/continue_interview")
async def continue_interview(message: str = Query(...), checkpoint_id: str = Query(...)):
    config = {
        "configurable": {
            "thread_id": checkpoint_id
        }
    }

    async def event_stream():
        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v2"
        )

        async for event in events:
            event_type = event["event"]

            if event_type == "on_chat_model_stream":
                content = serialise_ai_message_chunk(event["data"]["chunk"])
                safe_content = content.replace("\n", "\\n").replace('"', '\\"')
                yield f"data: {{\"type\": \"content\", \"content\": \"{safe_content}\"}}\n\n"

            elif event_type == "on_node_end" and event.get("name") == "score_session":
                msg = event["data"]["messages"][-1].content
                yield f"data: {{\"type\": \"score\", \"content\": \"{msg}\"}}\n\n"

            elif event_type == "on_node_end" and event.get("name") == "compare_sessions":
                msg = event["data"]["messages"][-1].content
                yield f"data: {{\"type\": \"comparison\", \"content\": \"{msg}\"}}\n\n"

        yield f"data: {{\"type\": \"end\"}}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
