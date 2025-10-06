from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate


deepseek = ChatOllama(
    base_url="http://localhost:11434",
    model="deepseek-r1:1.5b"
)


# 初始化对话历史
messages = [
    HumanMessage(content="你好！"),
    AIMessage(content="你好！有什么可以帮助你的？"),
    HumanMessage(content="推荐一本科幻小说。")
]

# query = ''
# while query != 'q':
#     response = deepseek.invoke(ChatPromptTemplate.from_template(messages[-1]))
#     print('AI: ', response.content)
#     messages.append(AIMessage(content=response.content))
#     query = input('Human: (输入"q"退出)')
#     messages.append(HumanMessage(content=query))

response = deepseek.invoke('你好')
print('AI: ', response.content)