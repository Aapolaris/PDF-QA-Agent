import asyncio

from prompts.summary import map_prompt, reduce_prompt
from utils.types import SummaryOverallState, SummaryState
from config import llm, Args, get_vector_store
from langgraph.types import Send
from langchain_core.documents import Document
from langchain.chains.combine_documents.reduce import split_list_of_docs, acollapse_docs
from typing import List
from langgraph.graph import START, END, StateGraph
from ingestion.get_file_chunks import ingest_file_chunks

args = Args()
# semaphore = asyncio.Semaphore(3)


async def generate_summary(state: SummaryState):
    """ Generate a summary of each piece of content """
    # async with semaphore:
    prompt = map_prompt.invoke({'context': state['content']})
    response = await llm.ainvoke(prompt)
    return {"summaries": [response.content]}


def map_summaries(state: SummaryOverallState):
    return [
        Send('generate_summary', {'content': content}) for content in state['contents']
    ]


def collect_summaries(state: SummaryOverallState):
    return {
        'collapsed_summaries': [Document(summary) for summary in state['summaries']]
    }


async def _reduce(input: List[Document]):
    # async with semaphore:
    prompt = reduce_prompt.invoke(input)
    response = await llm.ainvoke(prompt)
    return response.content


def length_function(documents: List[Document]):
    return sum(llm.get_num_tokens(doc.page_content) for doc in documents)


async def collapse_summaries(state: SummaryOverallState):
    doc_lists = split_list_of_docs(
        state['collapsed_summaries'], length_func=length_function, token_max=args.max_token
    )
    results = []
    # async with semaphore:
    for doc_list in doc_lists:
        results.append(await acollapse_docs(doc_list, _reduce))
    return {'collapsed_summaries': results}


def should_collapse(state: SummaryOverallState):
    num_tokens = length_function(state['collapsed_summaries'])
    if num_tokens > args.max_token:
        return 'collapse_summaries'
    else:
        return 'generate_final_summary'


async def generate_final_summary(state: SummaryOverallState):
    response = await _reduce(state['collapsed_summaries'])
    return {'final_summary': response}


def build_summary_graph(VectorStore):
    global vector_store
    vector_store = VectorStore
    graph = StateGraph(SummaryOverallState)

    graph.add_node('generate_summary', generate_summary)
    graph.add_node('collect_summaries', collect_summaries)
    graph.add_node('collapse_summaries', collapse_summaries)
    graph.add_node('generate_final_summary', generate_final_summary)

    graph.add_conditional_edges(START, map_summaries, ['generate_summary'])
    graph.add_edge('generate_summary', 'collect_summaries')
    graph.add_conditional_edges('collect_summaries', should_collapse)
    graph.add_conditional_edges('collapse_summaries', should_collapse)
    graph.add_edge('generate_final_summary', END)

    return graph.compile()


async def test():
    docs = ingest_file_chunks('../data/example.pdf')
    print(f"there are {len(docs)} documents after chunk")

    global vector_store
    if args.for_test:
        vector_store = get_vector_store()
    _ = vector_store.add_documents(docs)
    app = build_summary_graph(vector_store)
    step = None
    async for step in app.astream(
            {"contents": [doc.page_content for doc in docs]},
            {"recursion_limit": 10},
    ):
        print(list(step.keys()))
    print(step)


if __name__ == '__main__':
    asyncio.run(test())

