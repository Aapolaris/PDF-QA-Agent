import os
from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama

# 【注意】 如果使用Ollama的模型，代理请使用规则模式
# 所有外网请求都走代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'


class Args:
    def __init__(self):
        self.max_token = 1500
        self.chunk_size = 1500
        self.chunk_overlap = 50
        self.pdf_file_path = 'data/example.docx'
        self.use_model_way = 'api'
        self.CHROMA_PERSIST_DIR = "data/CHROMA_PERSIST"
        self.UPLOAD_FOLDER = "data/UPLOAD_FOLDER"
        self.for_test = False
        self.mysql_user = 'root'
        self.mysql_password = os.environ.get('MYSQL_PASSWORD')
        self.mysql_database = 'qa_agent_mvp'


args = Args()

# os.environ['LANGSMITH_TRACING'] = 'True'
llm = None
if args.use_model_way == 'api':
    os.environ.get('GOOGLE_API_KEY')

    llm = init_chat_model("gemini-2.5-flash", model_provider='google-genai')
else:
    llm = ChatOllama(
        base_url='http://localhost:11434',
        model='llama3.2:latest',
    )

embeddings = HuggingFaceEmbeddings(
    model_name="D:/PersonalLearning/20250926_LangChian/PersonalKnowledgeBase/sentence-transformers-all-mpnet-base-v2"
)


def get_vector_store():
    vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory="./data/chroma_langchain_db",
    )
    return vector_store
