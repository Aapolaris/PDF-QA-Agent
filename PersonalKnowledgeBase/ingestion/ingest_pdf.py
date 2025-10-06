from config import Args
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

args = Args()


def ingest_pdf_chunks(pdf_file) -> List[Document]:
    loader = PyPDFLoader(pdf_file)
    documents = loader.load()
    context = ""
    for doc in documents:
        context += doc.page_content

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    all_splits = text_splitter.split_text(context)

    all_docs = [Document(doc) for doc in all_splits]
    return all_docs


if __name__ == "__main__":
    splits = ingest_pdf_chunks(pdf_file='../data/DeepLearning.pdf')
    print(splits[0])