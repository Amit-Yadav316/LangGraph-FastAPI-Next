from langgraph.graph import add_messages, StateGraph, END
from langgraph.checkpoint.redis import RedisCheckpointSaver
from langgraph.types import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.schema import Document
from dotenv import load_dotenv
from typing import Optional, List
from config import settings

from utils import vectorstore

checkpointer = RedisCheckpointSaver.from_url(settings.redis_url)


llm = ChatOpenAI(model="gpt-4o")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    name : str
    interview_type: str
    answers: List[str]
    question_count: int
    max_questions: int
    user_id: str
    session_id: str
    score: Optional[int]
    previous_session: Optional[Document]

async def start_interview(state: State):
    intro = f"You are an expert interviewer,Start with introducing youself to {state['name']} and ask the first question on {state['interview_type']}."
    return {"messages": [HumanMessage(content=intro)]}

async def model(state: State):
    result = await llm.ainvoke(state["messages"])
    return {"messages": [result]}

async def store_answer(state: State):
    user_response = state["messages"][-1].content
    state["answers"].append(user_response)
    state["question_count"] += 1
    return {"messages": []}

async def check_continue(state: State):
    if state["question_count"] < state["max_questions"]:
        return "model"
    return "score_session"

async def score_session(state: State):
    joined = "\n\n".join(state["answers"])
    prompt = f"Evaluate the following responses for a {state['interview_type']} interview. Give a score out of 10 in score/10 format and feedback in 50 words:\n\n{joined}"
    result = await llm.ainvoke([HumanMessage(content=prompt)])
    state["score"] = extract_score(result.content)

    doc = Document(
        page_content=result.content,
        metadata={
            "user_id": state["user_id"],
            "interview_type": state["interview_type"],
            "score": state["score"],
            "session_id": state["session_id"]
        }
    )
    vectorstore.add_documents([doc])

    return {"messages": [result]}

async def check_previous_sessions(state: State):
    previous_docs = vectorstore.similarity_search(
        "interview feedback",
        filter={"user_id": state["user_id"], "interview_type": state["interview_type"]},
        k=5
    )

    if previous_docs:
        combined_content = "\n\n".join([doc.page_content for doc in previous_docs])
        combined_doc = Document(
            page_content=combined_content,
            metadata={"combined": True}
        )
        state["previous_session"] = combined_doc
        return "compare_sessions"
    return END

async def compare_sessions(state: State):
    new_feedback = state["messages"][-1].content
    prev = state.get("previous_session")
    if not prev:
        return {"messages": [HumanMessage(content="No previous session to compare.")]}

    prompt = f"""
Compare these previous interviews:
{prev.page_content}

With this new interview:
Score: {state['score']}
Feedback: {new_feedback}

Provide a detailed comparison and performance report.
"""
    result = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"messages": [result]}


def extract_score(text: str) -> int:
    import re
    match = re.search(r"(\d+(\.\d+)?)/?10", text)
    if match:
        return int(float(match.group(1)))
    return 0


graph_builder = StateGraph(State)

graph_builder.add_node("start_interview", start_interview)
graph_builder.add_node("model", model)
graph_builder.add_node("store_answer", store_answer)
graph_builder.add_node("check_continue", check_continue)
graph_builder.add_node("score_session", score_session)
graph_builder.add_node("check_previous_sessions", check_previous_sessions)
graph_builder.add_node("compare_sessions", compare_sessions)

graph_builder.set_entry_point("start_interview")

graph_builder.add_edge("start_interview", "model")
graph_builder.add_edge("model", "store_answer")
graph_builder.add_edge("store_answer", "check_continue")

graph_builder.add_conditional_edges("check_continue", {
    "model": "model",
    "score_session": "score_session"
})

graph_builder.add_edge("score_session", "check_previous_sessions")
graph_builder.add_conditional_edges("check_previous_sessions", {
    "compare_sessions": "compare_sessions",
    END: END
})

graph = graph_builder.compile(checkpointer=checkpointer)
