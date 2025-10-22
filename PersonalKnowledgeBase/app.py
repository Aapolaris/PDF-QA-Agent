import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import nest_asyncio
import uuid
import logging
import threading
from langchain_core.messages import AIMessage, HumanMessage

from config import Args
from utils.database_operation import (load_data_from_mysql, create_chroma_for_docs, save_conversation_to_mysql,
                                      delete_session_in_mysql, delete_session_in_chroma)
from ingestion.get_file_chunks import ingest_file_chunks
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
#   "metadatas": {filename, uploaded_at}
# }
SESSIONS = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data():
    """initialize the SESSIONS"""
    SESSIONS = load_data_from_mysql()
    for session_id, session in SESSIONS.items():
        session["app_agent"] = build_agent_for_session(session["vector_store"])
    return SESSIONS


def build_agent_for_session(vector_store):
    """
    Try to build an orchestrator/agent that uses the per-session vector_store.
    :param vector_store:
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
        docs = ingest_file_chunks(save_path)
    except Exception as e:
        logger.exception("Failed to ingest file: %s", e)
        return jsonify({"error": "Failed to ingest file", "details": str(e)}), 500

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
        agent = build_agent_for_session(vector_store)
    except Exception as e:
        logger.exception("Failed to build agent: %s", e)
        return jsonify({"error": "Failed to build agent", "details": str(e)}), 500

    # Save session info
    SESSIONS[session_id] = {
        "vector_store": vector_store,
        "app_agent": agent,
        "docs": docs,
        "history": [],
        "metadatas": {"filename": filename}
    }
    logger.info("Created session %s for file %s (%d docs)", session_id, filename, len(docs))

    return jsonify({
        "message": "PDF uploaded and processed",
        "session_id": session_id,
        "filename": filename,
        "pages": len(docs)
    }), 200


# Create a persistent event loop in a background thread
background_loop = asyncio.new_event_loop()


def loop_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=loop_thread, args=(background_loop,), daemon=True).start()


def run_async(coro):
    """Submit coroutine to the persistent event loop thread and wait for result."""
    future = asyncio.run_coroutine_threadsafe(coro, background_loop)
    return future.result()


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

    try:
        result = run_async(run_agent())
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "agent execution failed", "details": str(e)}), 500

    if result['task'] == 'summarize':
        answer = result['final_summary']
    else:
        answer = result['final_answer']

    logger.info("Session %s answered: %s", session_id, answer[:120].replace("\n", " "))

    # Save history (keep minimal)
    session["history"] = session.get("history", []) + [
        HumanMessage(content=question),
        AIMessage(content=answer),
    ]

    result = save_conversation_to_mysql(session_id, session)
    if result is not None:
        session['vector_store'] = result

    return jsonify({"answer": answer}), 200


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """
    Return a list of active sessions (id + metadata)
    """
    global SESSIONS
    SESSIONS = load_data()
    word_map = {'ai': 'assistant', 'human': 'user'}
    out = []
    for sid, s in SESSIONS.items():
        out.append({
            "session_id": sid,
            "filename": s.get("metadatas", {}).get("filename"),
            "messages": [{"role": word_map[msg.type], "content": msg.content} for msg in s['history']]
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

    delete_session_in_mysql(session_id)
    logging.info("Deleting specific session from mysql")
    delete_session_in_chroma(session_id)
    logging.info("Deleting specific session from chroma")
    del SESSIONS[session_id]  # 移除会话入口
    logger.info("Successfully deleted session: %s", session_id)

    return jsonify({"message": "Session deleted"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
