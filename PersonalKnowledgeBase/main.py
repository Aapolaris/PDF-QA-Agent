import asyncio
from config import llm, embeddings, Args, get_vector_store
from ingestion.get_file_chunks import ingest_file_chunks
from graphs.orchestrator import build_orchestrator


async def main(args):
    # 1. 提取pdf内容
    docs = ingest_file_chunks(args.pdf_file_path)
    vector_store = get_vector_store()
    _ = vector_store.add_documents(docs)

    # 2. 获取agent
    app = build_orchestrator(vector_store)

    state = {
        'task': '',
        'query': '',
        'contents': docs,
        'final_summary': '',
        'final_answer': '',
        'history': []
    }

    query = ""
    config = {'configurable': {'thread_id': '0001'}}
    while query != "q":
        query = input("human: ")
        if query == "q":
            break

        state['query'] = query
        result = await app.ainvoke(state, config)

        if result['task'] == 'summarize':
            print(result['final_summary'])
        else:
            print(result['final_answer'])


if __name__ == '__main__':
    args = Args()
    asyncio.run(main(args))

