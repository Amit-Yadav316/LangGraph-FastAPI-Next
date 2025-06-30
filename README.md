## PERPLEX(AI INTERVIEWER)
![Screenshot 2025-06-26 101317](https://github.com/user-attachments/assets/c976b5d4-1b4c-4cf3-9368-555bc20288cd)
# AI Interviewer

An AI-powered interviewer capable of conducting topic-specific, intelligent conversations using LangGraph, Retrieval-Augmented Generation (RAG), and Pinecone. Designed for dynamic, interactive experiences with streaming responses via HTTP — no WebSocket required.

Built using:

- LangGraph for LLM-driven conversational flows
- Pinecone for semantic memory and context retrieval
- FastAPI backend with streaming HTTP responses
- Next.js frontend with real-time rendering
- OpenAI GPT-4/GPT-4o for intelligent question generation

---

## Features

- Topic-aware AI interviewer sessions
- Streaming responses using HTTP 
- Contextual memory with Pinecone and Redis
- Real-time follow-up question generation
- Session-based memory management
- Tool-augmented LangGraph agent with RAG

---

## Tech Stack

**Backend:**
- LangGraph (agent state machine over LangChain)
- Pinecone (vector similarity search)
- Redis (short-term memory and checkpoints)
- FastAPI (RESTful API with streaming response support)

**Frontend:**
- Next.js with React
- HTTP streaming via `ReadableStream` (no polling or sockets)
- Tailwind CSS for styling
