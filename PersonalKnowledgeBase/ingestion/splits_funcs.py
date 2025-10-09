from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownTextSplitter
from config import Args

args = Args()


def split_text_1(context):
    """使用递归字符分割法对文本进行分割"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    if type(context) == str:
        all_splits = text_splitter.split_text(context)
    else:
        all_splits = text_splitter.split_documents(context)
    return all_splits


def split_text_2(md_pages):
    """使用MarkdownTextSplitter拆分markdown文本"""
    text_splitter = MarkdownTextSplitter(
        chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap
    )
    all_splits = text_splitter.split_documents(md_pages)
    return all_splits