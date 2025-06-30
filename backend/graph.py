from langgraph.graph import add_messages, StateGraph, END
from langgraph.checkpoint.redis import RedisCheckpointSaver
from langgraph.types import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
from typing import Optional, List
import os
import ast

load_dotenv()


redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
checkpointer = RedisCheckpointSaver.from_url(redis_url)


class State(TypedDict):
    messages: Annotated[list, add_messages]


search_tool = TavilySearchResults(max_results=4)
tools = [search_tool]


llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools=tools)


async def model(state: State):
    result = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [result]}


async def tools_router(state: State):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tool_node"
    else:
        return END


async def tool_node(state: State):
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name == "tavily_search_results_json":
            search_results = await search_tool.ainvoke(tool_args)

            tool_message = ToolMessage(
                content=str(search_results),
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
    return {"messages": tool_messages}

async def summarize_search_node(state: State):
    tool_msg = state["messages"][-1]
    try:
        results = ast.literal_eval(tool_msg.content)
    except Exception:
        results = []

    summary_prompt = "Summarize the following news updates about Real Madrid:\n\n"
    for item in results:
        summary_prompt += f"Title: {item.get('title', '')}\nSnippet: {item.get('content', '')}\n\n"

    summary_llm = ChatOpenAI(model="gpt-4o", streaming=True)
    response = await summary_llm.ainvoke([HumanMessage(content=summary_prompt)])
    return {"messages": [response]}


graph_builder = StateGraph(State)

graph_builder.add_node("model", model)
graph_builder.add_node("tool_node", tool_node)
graph_builder.add_node("summarize_search", summarize_search_node)

graph_builder.set_entry_point("model")

graph_builder.add_conditional_edges("model", tools_router)
graph_builder.add_edge("tool_node", "summarize_search")
graph_builder.add_edge("summarize_search", "model")


graph = graph_builder.compile(checkpointer=checkpointer)
