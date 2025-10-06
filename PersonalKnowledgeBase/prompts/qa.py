from langchain_core.prompts import ChatPromptTemplate

system_prompt = (
    "You are as assistant for question-answer task. "
    "Use the retrieved context to answer the question."
    "If unknown, say you don't know. Max three sentences. Be concise.\n\n{context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ('system', system_prompt),
    ('human', "{query}")
])