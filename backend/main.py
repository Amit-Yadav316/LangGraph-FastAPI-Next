from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import start_interview, continue_interview

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


app.include_router(start_interview.router)
app.include_router(continue_interview.router)