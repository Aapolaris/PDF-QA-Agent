import re
from typing import List
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from langchain_core.documents import Document

from config import Args
from ingestion.splits_funcs import split_text_1, split_text_2

args = Args()


def ingest_file_chunks(file_name):
    if file_name.endswith('.pdf'):
        return ingest_pdf_chunks(file_name)
    elif file_name.endswith('.md'):
        return ingest_md_chunks(file_name)
    elif file_name.endswith(('doc', 'docx')):
        return ingest_word_documents(file_name)


def ingest_pdf_chunks(pdf_file) -> List[Document]:
    """使用UnstructuredPDFLoader 或 PyPDFLoader解析pdf文档"""
    try:
        loader = UnstructuredPDFLoader(pdf_file)  # 在一些复杂文档比如./data/2024190948.pdf中表现较好
        print("use UnstructuredPDFLoader")
    except:
        loader = PyPDFLoader(pdf_file)
        print("use PyPDFLoader")
    documents = loader.load()
    # context = ""
    # for doc in documents:
    #     context += doc.page_content

    all_docs = split_text_1(documents)

    # all_docs = [Document(doc) for doc in all_splits]
    return all_docs


def ingest_md_chunks(md_file):
    loader = UnstructuredMarkdownLoader(md_file)
    md_pages = loader.load()
    all_docs = split_text_2(md_pages)
    return all_docs


def ingest_word_documents(doc_file):
    loader = UnstructuredWordDocumentLoader(doc_file, mode='single')
    context = loader.load()
    all_docs = split_text_1(context)
    return all_docs


if __name__ == "__main__":
    splits = ingest_file_chunks(file_name="../data/2024190948.pdf")
    print(splits[0])