from langchain_core.prompts import ChatPromptTemplate


system_prompt = (
    "You are an assistant for question-answer task. \n"
    "Answer the user's questions based on the chat history provided (may be empty).\n"
    "If needed, you can use the `retrieve` tool to find relevant information before you answer the question\n"
    "Do not make up answers. If unknown, say you don't know.\n"

)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "questions: {input} \n\nchat history: \n{chat_history}")
])


if __name__ == "__main__":
    prompt = qa_prompt.invoke({
        'input': 'this is the question.',
        'chat_history': ''
    })
    print(prompt.to_messages())