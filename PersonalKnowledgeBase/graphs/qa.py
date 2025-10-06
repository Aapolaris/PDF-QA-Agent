from prompts.qa import qa_prompt
from config import llm
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from ingestion.ingest_pdf import ingest_pdf_chunks

vector_store = None

@tool(response_format='content')
def retrieve(query: str):
    """ retrieve information related to the query """
    retrieved_docs = vector_store.similarity_search(query, k=2)  # 取连两个最相似的文档
    retrieved_contents = "\n\n".join(
        f"Content: {doc.page_content}\n\n" for doc in retrieved_docs
    )
    return retrieved_contents


def build_qa_agent(VectorStore):
    global vector_store
    vector_store = VectorStore
    memory = MemorySaver()
    agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)

    return agent_executor


if __name__ == '__main__':
    docs = ingest_pdf_chunks('../data/example.pdf')
    _ = vector_store.add_documents(docs)
    app = build_qa_agent()
    config = {"configurable": {'thread_id': '0001'}}
    for event in app.stream(
            {"messages": [{"role": "user", "content": 'k-means算法中的k如何选择？'}]},
            stream_mode="values",
            config=config,
    ):
        event["messages"][-1].pretty_print()

