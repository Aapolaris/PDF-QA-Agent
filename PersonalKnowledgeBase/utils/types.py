from typing import TypedDict, List, Annotated, Literal
import operator
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage


class SummaryOverallState(TypedDict):
    contents: List[str]
    summaries: Annotated[list, operator.add]
    collapsed_summaries: List[Document]
    final_summary: str


class SummaryState(TypedDict):
    content: str


class OrchestratorState(TypedDict):
    task: Literal['summarize', 'qa']
    query: str
    contents: List[Document]
    final_summary: str
    final_answer: str
    history: Annotated[List[BaseMessage], operator.add]