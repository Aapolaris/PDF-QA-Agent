from utils.types import OrchestratorState
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from prompts.intent import intent_prompt
from config import llm
from graphs.summary import build_summary_graph
from graphs.qa import build_qa_agent


async def judge_task(state: OrchestratorState):
    prompt = intent_prompt.invoke({'query': state['query']})
    resp = await llm.ainvoke(prompt)
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
        return {'final_summary': result['final_summary']}

    async def run_qa_task(state: OrchestratorState):
        result = await qa_agent.ainvoke({
            'messages': state['query']
        })
        return {
            'final_answer': result['messages'][-1].content,
            # 'history': [HumanMessage(content=state['query']), AIMessage(content=result['messages'][-1])]
        }

    graph.add_node('summarize', run_summary_task)
    graph.add_node('qa', run_qa_task)

    graph.add_conditional_edges(START, judge_task, ['summarize', 'qa'])
    graph.add_edge('summarize', END)
    graph.add_edge('qa', END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
