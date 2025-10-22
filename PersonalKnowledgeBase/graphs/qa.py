from prompts.qa import qa_prompt
from config import llm, get_vector_store, Args
from ingestion.get_file_chunks import ingest_file_chunks

from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent


args = Args()


@tool(response_format='content')
def retrieve_docs(query: str):
    """ retrieve information in passage related to the query """
    retrieved_docs = vector_store.similarity_search(query, k=2, filter={"type": "documents"})  # 取连两个最相似的文档
    retrieved_contents = "\n\n".join(
        f"Content: {doc.page_content}\n\n" for doc in retrieved_docs
    )
    return retrieved_contents


@tool(response_format='content')
def retrieve_long_term_memory(query: str):
    """retrieve the long term memory related to the query """
    retrieved = vector_store.similarity_search(query, k=2, filter={"type": "memory"})
    retrieved_contents = "\n\n".join(
        f"the key information about the long term memory:\n\n{content}"
        for content in retrieved
    )
    return retrieved_contents


def build_qa_agent(VectorStore, test=True):
    global vector_store
    vector_store = VectorStore
    if args.for_test:
        memory = MemorySaver()
        agent_executor = create_react_agent(llm, [retrieve_docs, retrieve_long_term_memory], memory)
    else:
        agent_executor = create_react_agent(llm, [retrieve_docs, retrieve_long_term_memory])

    return agent_executor


if __name__ == '__main__':
    docs = ingest_file_chunks('../data/2024190948.pdf')
    vector_store = get_vector_store()
    _ = vector_store.add_documents(docs)
    app = build_qa_agent(vector_store, test=True)
    config = {"configurable": {'thread_id': '0001'}}
    for event in app.stream(
            {"messages": [{"role": "user", "content": 'how to select k in k-means algorithm'}]},
            stream_mode="values",
            config=config,
    ):
        event["messages"][-1].pretty_print()

