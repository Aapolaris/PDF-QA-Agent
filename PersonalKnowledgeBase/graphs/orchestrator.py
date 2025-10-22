from utils.types import OrchestratorState
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from prompts.intent import intent_prompt
from prompts.qa import qa_prompt
from config import llm
from graphs.summary import build_summary_graph
from graphs.qa import build_qa_agent


def format_chat_history(history):
    if not history:
        return "No prior conversation."
    try:
        content = "\n".join(f"{msg.type}: {msg.content}\n" for msg in history[-10:])
    except Exception as e:
        print(history)
    return content


async def judge_task(state: OrchestratorState):
    prompt = intent_prompt.invoke({'query': state['query']})
    resp = await llm.ainvoke(prompt.to_messages())
    intent = resp.content.strip().lower()
    if 'summarize' in intent or 'summary' in intent:
        state['task'] = 'summarize'
        return 'summarize'
    state['task'] = 'qa'
    return 'qa'


def build_orchestrator(vector_store):
    summary_graph = build_summary_graph(vector_store)
    qa_agent = build_qa_agent(vector_store)

    graph = StateGraph(OrchestratorState)

    async def run_summary_task(state: OrchestratorState):
        contents = [d.page_content for d in state['contents']]
        result = await summary_graph.ainvoke({
            'contents': contents
        })
        return {
            'task': 'summarize',
            'final_summary': result['final_summary'],
        }

    async def run_qa_task(state: OrchestratorState):
        prompt = qa_prompt.invoke({
            'input': state['query'],
            'chat_history': state['history']
        })
        result = await qa_agent.ainvoke({'messages': prompt.to_messages()})
        return {
            'task': 'qa',
            'final_answer': result['messages'][-1].content,
            'history': [HumanMessage(content=state["query"]), result["messages"][-1]]
        }

    graph.add_node('summarize', run_summary_task)
    graph.add_node('qa', run_qa_task)

    graph.add_conditional_edges(START, judge_task, ['summarize', 'qa'])
    graph.add_edge('summarize', END)
    graph.add_edge('qa', END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
