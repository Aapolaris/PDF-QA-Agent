import os
import shutil
import mysql.connector
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_chroma import Chroma

from prompts.extract_key_info import extract_key_info_prompt
from config import llm, embeddings, Args

args = Args()
DB_CONFIG = {
    "host": "localhost",
    "user": args.mysql_user,
    "password": args.mysql_password,
    "database": args.mysql_database,
}


def create_chroma_for_docs(docs, session_id):
    """
    Create (or reuse) a Chroma collection for this session and add documents.
    :param docs:
    :param session_id:
    :return:
    """
    chroma_vs = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=session_id,
        persist_directory=args.CHROMA_PERSIST_DIR
    )
    return chroma_vs


def load_data_from_chroma(session_id, data_type='documents', persist_dir=args.CHROMA_PERSIST_DIR):
    """
    load vector_store, docs from chroma and create app_agent for this session.
    :return:
    """
    vector_store = Chroma(
        embedding_function=embeddings,
        collection_name=session_id,
        persist_directory=persist_dir
    )
    # print(vector_store._collection.count())
    result = vector_store.get(
        where={"type": data_type},
        include=["documents", "metadatas"]
    )
    documents = result["documents"]
    metadatas = result["metadatas"]
    docs = []
    for doc, metadata in zip(documents, metadatas):
        docs.append(Document(page_content=doc, metadata=metadata))
    # print(docs)
    return vector_store, docs


def load_data_from_mysql():
    """
    load history, metadata from mysql database
    :return SESSIONS[session_id] = {"history": List[BaseMessage], "metadata": {"filename": "filename"}}
    """
    print("log: 试图从mysql读取数据")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT session_id, role, content, filename, created_at
        FROM chat_history
        ORDER BY session_id, created_at
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    SESSIONS = {}
    for row in rows:
        sid = row["session_id"]
        if sid not in SESSIONS:
            vector_store, docs = load_data_from_chroma(sid)
            SESSIONS[sid] = {"vector_store": vector_store, "docs": docs, "history": [], "metadatas": {}}
            SESSIONS[sid]["metadatas"]["filename"] = row["filename"]

        if row['role'] == "human":
            SESSIONS[sid]["history"].append(HumanMessage(row["content"]))
        else:
            SESSIONS[sid]["history"].append(AIMessage(row["content"]))

    cursor.close()
    conn.close()

    return SESSIONS


def insert_message(session_id, role, content, filename=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, role, content, filename)
        VALUES (%s, %s, %s, %s)
    """, (session_id, role, content, filename))
    conn.commit()
    cursor.close()
    conn.close()


def add_long_term_memory(histories, vector_store):
    """extract key information from the last 10 chat messages and store it into chroma"""
    print("log:试图把聊天历史转化为长期记忆")
    content = "\n"
    for msg in histories:
        content += f"{msg.type}: {msg.content}\n"
    prompt = extract_key_info_prompt.invoke({"history": content})
    answer = llm.invoke(prompt)
    vector_store.add_texts([answer.content], metadatas=[{"type": "lang-term-memory"}])
    return vector_store


def save_conversation_to_mysql(session_id, session):
    """
    save conversation to mysql database and turn the last 10 new chat message into long-term memory
    :return None or session['vector_store'], the latter if there are some updates in vector_store
    """
    print("log: 试图把数据写入mysql")
    insert_message(session_id, session["history"][-2].type,
                   session["history"][-2].content, session["metadatas"]["filename"])
    insert_message(session_id, session["history"][-1].type,
                   session["history"][-1].content, session["metadatas"]["filename"])
    if len(session["history"]) % 10 == 0:
        session["vector_store"] = add_long_term_memory(session["history"][-10:], session['vector_store'])
        return session["vector_store"]
    return None


def delete_session_in_mysql(session_id):
    """
    Delete all chat records associated with a specific session_id.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = "DELETE FROM chat_history WHERE session_id = %s"
    cursor.execute(query, (session_id,))

    conn.commit()
    cursor.close()
    conn.close()


def delete_session_in_chroma(session_id):
    """directly delete all chat records associated with a specific session_id."""
    # 物理删除存储embeddings的文件，尽管.sqlite3中仍有元数据信息
    target_dir = os.path.join(args.CHROMA_PERSIST_DIR, session_id)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)


def test():
    docs = [
        Document(page_content="北京是中国的首都。", metadata={"source": "wiki", "type": "documents"}),
        Document(page_content="上海是中国的经济中心。", metadata={"source": "wiki", "type": "documents"}),
        Document(page_content="广州以美食闻名。", metadata={"source": "wiki", "type": "documents"}),
    ]
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="demo_collection",
        persist_directory=args.CHROMA_PERSIST_DIR
    )
    vector_store.add_texts(["这是新加入的数据"], metadatas=[{"type": "memory"}])
    print("成功存储")
    vector_store, chat_data = load_data_from_chroma("demo_collection")
    print(chat_data)


if __name__ == "__main__":
    # test()
    # delete_session_in_chroma("6095ea36-2a38-47b1-bd0a-509ef452ce20")
    vector_store, chat_data = load_data_from_chroma(session_id="785ddfd8-6e4b-4820-9fd9-67f0196d141e",
                                                    data_type="lang-term-memory",
                                                    persist_dir="../data/CHROMA_PERSIST")
    print(chat_data)