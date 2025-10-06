from  langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


map_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a careful summarizer."),
    ("human", "Write a concise summary of the following:\n\n{context}")
])

reduce_template = """
The following is a set of summaries:
{docs}
Take these and distill it into a final, consolidated summary
of the main themes.
"""

reduce_prompt = ChatPromptTemplate([("human", reduce_template)])