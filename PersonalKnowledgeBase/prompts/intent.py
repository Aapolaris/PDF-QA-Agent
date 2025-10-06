from langchain_core.prompts import ChatPromptTemplate

intent_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a classifier. Decide whether the user query is asking for a SUMMARY of the whole document "
     "or a QUESTION about specific details. "
     "Output only one word: 'summarize' or 'qa'."),
    ("human", "{query}")
])