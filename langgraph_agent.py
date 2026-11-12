import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from agent_tools import get_order_status, process_refund

load_dotenv()

tools = [get_order_status, process_refund]

# Configure High-Availability Model Routing to prevent 503 disruption
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    max_retries=1
).bind_tools(tools)

backup_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    max_retries=2
).bind_tools(tools)

llm_with_tools = primary_llm.with_fallbacks([backup_llm])

SYSTEM_PROMPT = """You are an autonomous Enterprise Customer Support Agent.
Your job is to help users check order statuses and process refunds.

CRITICAL OPERATING PROCEDURE:
1. Whenever a user asks for a refund, you MUST call `get_order_status` first to inspect the order's current status.
2. Only after verifying the status, call `process_refund` if appropriate, or explain why the refund cannot be processed.
3. Never guess or hallucinate order details. Rely strictly on the SQL tool outputs.
"""

def call_model(state: MessagesState):
    """Reasoning Node: Inspects current state and determines next action or tool call."""
    messages = state["messages"]
    
    # Inject system prompt if not present in the current thread state
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Action Node: Executes invoked tools and appends ToolMessages to the state
tool_node = ToolNode(tools)

# Construct ReAct State Machine Graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")

# Route to tools if LLM generates a tool call; route to END if final response is generated
workflow.add_conditional_edges("agent", tools_condition)

# Cyclical edge returning tool outputs to the reasoning node
workflow.add_edge("tools", "agent")

# Attach persistent memory checkpointer for multi-turn thread context
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def invoke_support_agent(user_input: str, thread_id: str) -> dict:
    """Executes the state machine and returns stripped response strings and execution metadata."""
    config = {"configurable": {"thread_id": thread_id}}
    
    final_state = app.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )
    
    last_message = final_state["messages"][-1]
    clean_reply = last_message.text if hasattr(last_message, "text") and last_message.text else str(last_message.content)
    
    tools_used = []
    for msg in reversed(final_state["messages"]):
        if msg.type == "human":
            break
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])
                
    tools_used.reverse()
    
    return {
        "thread_id": thread_id,
        "tools_executed": tools_used,
        "agent_response": clean_reply
    }

if __name__ == "__main__":
    from setup_db import create_dummy_database
    create_dummy_database()
    
    print("\n--- INITIATING LOCAL MULTI-TURN MEMORY TEST ---")
    
    turn1 = invoke_support_agent("Hi, this is Bob. Please refund my order ORD-102.", thread_id="session-bob-1")
    print(f"\nTurn 1 Tools Used: {turn1['tools_executed']}")
    print(f"Turn 1 Reply: {turn1['agent_response']}")
    
    turn2 = invoke_support_agent("What was the exact item name and dollar amount you just refunded me?", thread_id="session-bob-1")
    print(f"\nTurn 2 Tools Used: {turn2['tools_executed']}")
    print(f"Turn 2 Reply: {turn2['agent_response']}")