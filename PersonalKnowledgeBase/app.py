import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import nest_asyncio
import uuid
import logging
from langchain_community.vectorstores import Chroma
import chromadb

from config import embeddings, Args
from ingestion.ingest_pdf import ingest_pdf_chunks
from graphs.orchestrator import build_orchestrator
nest_asyncio.apply()

args = Args()

app = Flask(__name__)
CORS(app)

os.makedirs(args.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(args.CHROMA_PERSIST_DIR, exist_ok=True)

# Sessions store
# session_id -> {
#   "vector_store": <Chroma instance>,
#   "app_agent": <agent instance>,
#   "docs": <list of docs>,
#   "history": [ {role, content, ...}, ... ],
#   "metadata": {filename, uploaded_at}
# }
SESSIONS = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_chroma_for_docs(docs, session_id):
    """
    Create (or reuse) a Chroma collection for this session and add documents.
    :param docs:
    :param session_id:
    :return:
    """
    persist_dir = args.CHROMA_PERSIST_DIR

    chroma_vs = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=session_id,
        persist_directory=persist_dir,
    )

    try:
        chroma_vs.persist()
    except Exception:
        pass
    return chroma_vs


def build_agent_for_session(vector_store, session_id):
    """
    Try to build an orchestrator/agent that uses the per-session vector_store.
    :param vector_store:
    :param session_id:
    :return:
    """
    try:
        agent = build_orchestrator(vector_store)
        logger.info("build orchestrator for session {session_id}")
        return agent
    except Exception as e:
        logger.exception("Unexpected error while building orchestrator: %s", e)
        raise


@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Upload a pdf, ingest into documents, create a per-session Chroma collection and agent
    :return: { session_id, filename, pages }
    """

    if "file" not in request.files:
        return jsonify({"error": 'no file part'}), 400

    pdf_file = request.files['file']
    if pdf_file.filename == '':
        return jsonify({"error": 'no selected part'}), 400
    filename = pdf_file.filename
    save_path = os.path.join(args.UPLOAD_FOLDER, filename)
    pdf_file.save(save_path)
    logger.info(f"saved uploaded file to {save_path}")

    # Ingest and chunk PDF into documents (your helper)
    try:
        docs = ingest_pdf_chunks(save_path)
    except Exception as e:
        logger.exception("Failed to ingest PDF: %s", e)
        return jsonify({"error": "Failed to ingest PDF", "details": str(e)}), 500

    # create a new session
    session_id = str(uuid.uuid4())

    # Create Chroma vector store for this session
    try:
        vector_store = create_chroma_for_docs(docs, session_id)
    except Exception as e:
        logger.exception("Failed to create Chroma vector store: %s", e)
        return jsonify({"error": "Failed to create vector store", "details": str(e)}), 500

    # Build the agent for this session (attempt to pass vector_store)
    try:
        agent = build_agent_for_session(vector_store, session_id)
    except Exception as e:
        logger.exception("Failed to build agent: %s", e)
        return jsonify({"error": "Failed to build agent", "details": str(e)}), 500

    # Save session info
    SESSIONS[session_id] = {
        "vector_store": vector_store,
        "app_agent": agent,
        "docs": docs,
        "history": [],
        "metadata": {"filename": filename}
    }
    logger.info("Created session %s for file %s (%d docs)", session_id, filename, len(docs))

    return jsonify({
        "message": "PDF uploaded and processed",
        "session_id": session_id,
        "filename": filename,
        "pages": len(docs)
    }), 200


@app.route("/ask", methods=["POST"])
def ask_question():
    """
    Ask a question for a specific session
    :return: { question: '...', session_id: '...' }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": 'Invalid json body'}), 400
    question = data.get('question', '')
    session_id = data.get('session_id','')

    session = SESSIONS[session_id]
    app_agent = session["app_agent"]
    docs = session['docs']

    state = {
        'task': "",
        "query": question,
        "contents": docs,
        "final_answer": '',
        "final_summary": '',
        "history": session.get("history", []),
    }

    async def run_agent():
        config = {'configurable': {'thread_id': session_id}}
        result = await app_agent.ainvoke(state, config)
        return result

    # Run asynchronous agent invocation safely
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_agent())
    except Exception as e:
        logger.exception("Agent run failed: %s", e)
        return jsonify({"error": "Agent execution failed", "details": str(e)}), 500

    if result['task'] == 'summarize':
        answer = result['final_summary']
    else:
        answer = result['final_answer']

    # Save history (keep minimal)
    try:
        session["history"].append({"role": "user", "content": question})
        session["history"].append({"role": "assistant", "content": answer})
    except Exception:
        # In case history is not list or append fails
        session["history"] = session.get("history", []) + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ]

    logger.info("Session %s answered: %s", session_id, answer[:120].replace("\n", " "))

    return jsonify({"answer": answer}), 200


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """
    Return a list of active sessions (id + metadata)
    """
    out = []
    for sid, s in SESSIONS.items():
        out.append({
            "session_id": sid,
            "filename": s.get("metadata", {}).get("filename"),
            "messages": len(s.get("history", []))
        })
    return jsonify({"sessions": out}), 200


@app.route("/delete_session", methods=["POST"])
def delete_session():
    """
    Delete a session and its Chroma collection.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    if session_id not in SESSIONS:
        return jsonify({"error": "Unknown session_id"}), 400

    logger.info("Deleting session: %s", session_id)

    # 更彻底的 Chroma 集合删除
    try:
        persist_dir = args.CHROMA_PERSIST_DIR

        client = chromadb.PersistentClient(path=persist_dir)
        try:
            client.delete_collection(session_id)
            logger.info("Successfully deleted Chroma collection: %s", session_id)
        except Exception as e:
            logger.warning("Could not delete collection via client: %s", e)

    except Exception as e:
        logger.exception("Error while trying to clean vector store for session %s", session_id)
        # 不返回错误，继续删除会话信息

    # 移除会话入口
    del SESSIONS[session_id]

    logger.info("Successfully deleted session: %s", session_id)
    return jsonify({"message": "Session deleted"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
