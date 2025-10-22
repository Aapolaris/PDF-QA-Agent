from langchain_core.prompts import ChatPromptTemplate


extract_key_info_prompt_template = """
the following is a set of chat record between ai and human, 
you should extract important facts, preferences, or user-provided data that may be useful in future interactions.
Return them as concise bullet points.

{history}
"""

extract_key_info_prompt = ChatPromptTemplate([("human", extract_key_info_prompt_template)])

