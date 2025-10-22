[Prompt engineeringOverview](https://www.youtube.com/watch?v=dOxUroR57xs)

## 一、Prompt Engineering的介绍

#### 1. **prompt 的一般构成**
- Instructions
- Context
- Input data
- Output indicator

> 🌰
> classify the text into neutral, negative or positive
> Text: I think the food was okay.
> Sentiment:

#### 2. **基本参数设置**

- Temperature：值越高输出越随机，相反，越低则越具备确定性。
- top_p：模型考虑了具有 `top_n` 概率质量的 `token` 结果。`top_p` 能够提供一个广阔的概率范围供模型选择.

> 二者从不同角度影响输出，其中前者更偏向于控制输出的“随机性”，后者则是在给定的可能结果中设定一个“阈值”

**通常只修改其中一个，而不要同时此修改二者**


#### 3. **针对不同任务的模板示例**

##### 1）文本摘要

	( context ) ......
	( instructor ) 用一句话解释上面的内容
	( answer )

> 💡 **Tips**:
> 可以在 prompt 中说明重点关注部分；
> 也可以尝试用 "extract" 代替 "summarize"


##### 2）问答

	answer the question based on the context below. Keep the answer short and concise. Respond "Unsure about answer" if bot sure about the answer.
	
	Context: .......
	
	Question: ......
	
	Answer: 

##### 3）文本分类

	classify the text into neutral, negative or positive
	
	Text: I think the food was okay.
	
	Sentiment:

##### 4）角色扮演
	the following is a conversation with an AI research assistant. The assistant tone is technical and scientific.
	
	Human: Hello, who are you?
	AI: Greeting! I am an AI search assistant. How can I help you today?
	Human: Can you tell me about the creation of blackholes?
	AI: 

##### 5）代码生成

##### 6）推理

## 二、常用的prompt engineering高级技术

##### `Few-shot prompts`
	在prompt中添加若干示例以指导模型

##### `Chain-of-thought (CoT) prompting`
	告诉模型推理的过程。通常以 "Let's think step by step." 开始描述
	CoT又分为 zero-shot CoT 和 few-shot CoT
	这对需要推理的任务非常有效

##### `Self-Consistency`
	核心假设：假设每个复杂问题都可以有多种思路来推导出最终答案。
	self-consistency在算术和常识性问题上的推理具有优势
	1. 使用 CoT 提示语言模型；
	2. 从语言模型的解码器中采样，取代 CoT 提示中的“贪婪解码”，生成一组不同的推理路径；
	3. 在最终答案集中选择最一致的答案拿到聚合结果

##### `Knowledge Generation Prompting`
	知识生成提示是指，首先（利用few-shot）指导模型生成与用户输入有关的知识，然后将这些知识连同问题一起输入给模型预测答案
	这种方法在常识推理等任务上非常有效

##### `Program-aided Language Model (PAL)`
	虽然 LLM+CoT 可以很好地将一些复杂问题分为若干子问题进行逐步推理，但对于一些较为复杂的数学运算等，即便其对任务的分解和思考时正确的，仍然可能会存在计算错误。
	因此提出了PAL方法，先将复杂推理任务用大模型分解，其次让大模型生成python代码并基于解释器来实现计算
	
##### `ReAct`
	ReAct运行LLMs与外部工具交互来获取额外信息，从而给出更可靠和实际的回应。其中LLMs是以交错的方式生成推理轨迹和任务特定操作
