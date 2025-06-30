from fastapi import FastAPI, Query,StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app import generate_chat_responses

@app.get("/")
async def root():
    return {"message": "Welcome to the LangGraph FastAPI Chat Service!"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
    expose_headers=["Content-Type"], 
)


@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    return StreamingResponse(
        generate_chat_responses(message, checkpoint_id), 
        media_type="text/event-stream"
    )