from openai import OpenAI, AsyncOpenAI
from settings import get_llm_model,get_llm_base_url,API_KEY
client = OpenAI(
    base_url=get_llm_base_url(),
    api_key =API_KEY
)
async_client = AsyncOpenAI(
    base_url=get_llm_base_url(),
    api_key =API_KEY 
)

conversation_history = []

def chat_with_openai(user_message, callback=None):
    # 用户消息加入对话历史
    conversation_history.append({"role": "user", "content": user_message})
    
    # 调用OpenAI API，开启流式输出
    response = client.chat.completions.create(
        model=get_llm_model(),  # 模型名称（GPT-4等）
        messages=conversation_history,
        stream=True  # 启用流式输出
    )
    
    # 存储助手回复
    assistant_reply = ""
    
    # 遍历流式响应
    for chunk in response:
        if chunk.choices:
            delta =chunk.choices[0].delta
            if delta.content:
                # 实时打印并累积助手的内容
                text = delta.content
                if callback:
                    callback(text)
                else:
                    print(text, end="", flush=True)
                assistant_reply += text  # 累积完整回复
    
    # 将助手回复加入对话历史
    conversation_history.append({"role": "assistant", "content": assistant_reply})
    # 返回完整的助手回复
    return assistant_reply

async def async_chat_with_openai(user_message):

    # 用户消息加入对话历史
    conversation_history.append({"role": "user", "content": user_message})
    
    # 存储助手回复
    assistant_reply = ""

    # 调用OpenAI API，开启流式输出
    async for chunk in await async_client.chat.completions.create(
            model=get_llm_model(),  # 模型名称（GPT-4等）
            messages=conversation_history,
            stream=True  # 启用流式输出
        ):
        
        print(chunk, flush=True)
        if chunk.choices!=None:
            delta =chunk.choices[0].delta
            if delta.content!=None:
                # 实时打印并累积助手的内容
                text = delta.content
                #print(text, end="", flush=True)
                assistant_reply += text  # 累积完整回复
    
    # 将助手回复加入对话历史
    conversation_history.append({"role": "assistant", "content": assistant_reply})
    print("")
    # 返回完整的助手回复
    return assistant_reply

async def async_chat(messages, callback, session=None):
    stop_chat = False
    # 存储助手回复
    assistant_reply = ""

    # 调用OpenAI API，开启流式输出
    async for chunk in await async_client.chat.completions.create(
            model=get_llm_model(),  # 模型名称（GPT-4等）
            messages=messages,
            stream=True  # 启用流式输出
        ):
        if session is not None and session.stop_chat:
            stop_chat = True
            break
        if chunk.choices:
            delta =chunk.choices[0].delta
            if delta.content:
                text = delta.content
                #print(text, end="", flush=True)
                assistant_reply += text  # 累积完整回复
                await callback(text)
    return stop_chat

def chat(messages, callback):
    stop_chat = False
    # 存储助手回复
    assistant_reply = ""

    # 调用OpenAI API，开启流式输出
    for chunk in client.chat.completions.create(
            model=get_llm_model(),  # 模型名称（GPT-4等）
            messages=messages,
            stream=True  # 启用流式输出
        ):
        if chunk.choices:
            delta =chunk.choices[0].delta
            if delta.content:
                text = delta.content
                #print(text, end="", flush=True)
                assistant_reply += text  # 累积完整回复
                callback(text)
    return stop_chat

if __name__ == "__main__":
    info="""提示：与孤独症儿童语言交流练习
    背景信息

        孤独症儿童语言阶段：包括单字、短句和仿说。
        仿说：
            立即仿说：孩子听到某些句子后立即重复部分或全部内容。例如，大人问“你要喝水吗？”，孩子可能立刻重复“喝水吗？”。
            延宕仿说：孩子在一段时间后重复之前听到的内容，有时可能与当前情境无关。
        “加一”规则：通过在孩子已有语言基础上增加一个语言单位（如一个词或短语），引导他们逐步提升语言表达能力。例如，当孩子说“苹果”时，回应为“红色的大苹果”。

    练习目标

        扩展孩子的语言表达能力，使其更加丰富和完整。
        提供自然的模仿机会，帮助孩子学习新的词汇或语言结构。
        通过适当的引导，提升孩子在交流中的参与感与舒适感。

    Prompt：应用“加一”规则进行角色扮演

    你正在与一位孤独症儿童互动，请运用“加一”规则，通过以下对话场景逐步扩展孩子的语言能力。
    场景 1：描述事物

    孩子：苹果。
    你的回应：红色的大苹果。
    场景 2：引导选择

    孩子：糖果。
    你的回应：甜甜的黄色糖果。
    场景 3：描述情境

    孩子：车。
    你的回应：蓝色的小车在跑。
    场景 4：表达需求

    孩子：水。
    你的回应：凉凉的一杯水。
    注意事项

        适应孩子的语言水平：确保新增内容在孩子能够理解和模仿的范围内。
        保持自然互动：用简短、清晰的句子增加语言单位，避免让孩子感到压力。
        观察孩子的反应：如果孩子模仿你的新增语言单位，给予积极鼓励；如果没有模仿，可以尝试更简单的扩展。

    通过这类练习，帮助孩子逐步掌握更复杂的语言表达形式，同时增强他们的交流意愿与能力。
            """
    prompt="""修改后的 Prompt：

    你现在是一个医生，正在与一位孤独症儿童互动。儿童的语言水平处于单字、短句、仿说阶段。你的任务是根据对话情境，实时运用**“加一”规则**与儿童进行交流，以扩展他们的语言表达能力。
    规则说明

        “加一”规则：在孩子已有语言表达的基础上，增加一个语言单位（如形容词、短语等），引导他们学习更复杂的表达。
        目标：通过引导对话，让儿童逐步学会使用更多词汇和更丰富的句式，同时保持互动的自然性。

    你的角色要求

        实时交流：与孤独症儿童一问一答，不要模拟完整对话，需回应孩子可能的语言输出。
        互动性强：根据孩子的回应，调整你的语言扩展策略，以鼓励他们参与和模仿。
        保持耐心：即使孩子没有立即回应或出现仿说行为，继续用“加一”规则引导，避免过度复杂化。

    场景开始

        你的位置：在诊室内，和孩子进行简单的日常对话。
        任务：根据孩子的语言输入，灵活回应并引导下一步对话。

    例如：

        孩子：苹果。
        医生（你）：红色的大苹果。

    请根据孩子的每一句话进行回应，并尝试扩展他们的语言表达。你现在可以开始交流。"""
    example=Prompt="""提示：与孤独症儿童的角色扮演练习

    你是一家小商店的商家，你的任务是与一位孤独症儿童互动，鼓励他们逐步开口交流。这个孩子可能一开始不回应，或者只是重复你的话，甚至答非所问。你的角色是保持耐心、给予鼓励，并根据孩子的反应调整对话，逐步推进。以下是一个分步骤的场景指南：
    场景 1：问候孩子

    商家：“小朋友，你好呀！欢迎来到我的小店。”
    孩子：（没有回应）

        行动：孩子没有回应。保持耐心，尝试换一种方式继续引导。

    场景 2：引入物品

    商家：“你看，这里有很多好吃的糖果哦。糖果有各种颜色呢。”
    孩子：（看着糖果）

        行动：孩子虽然没有说话，但通过看向糖果表现出了兴趣。继续描述糖果或提出简单问题。

    场景 3：鼓励简单回应

    商家：“这个是红色的糖果，红色，red。红色的糖果很甜哦。”
    孩子：“红……红色。”

        行动：孩子重复了“红色”。认可他们的回应并继续引导对话。

    场景 4：鼓励更多话语

    商家：“对啦，你真聪明！那这个黄色的糖果呢？”
    孩子：“黄色。”

        行动：孩子回答了“黄色”。即使仍是简单重复，也要积极鼓励，并继续对话。

    场景 5：提出选择

    商家：“非常棒！那你想要哪个糖果呀？”
    孩子：“红色。”

        行动：孩子终于直接回答了问题。对此表示认可，并推进下一步。

    场景 6：解释价格

    商家：“好呀，那我把红色的糖果拿给你。这个糖果一块钱一个哦。一块钱。”
    孩子：“一块钱。”

        行动：孩子重复了“一块钱”。利用这个机会进一步引导。

    场景 7：完成互动

    商家：“你有一块钱吗？可以拿给我，我就把糖果给你。”
    孩子：（开始在口袋里找钱）

        行动：孩子尝试找钱并将其递给你。对他们的努力给予积极反馈。

    商家：“太好了，这是你的红色糖果。欢迎下次再来哦。”
    孩子：“再来。”
    练习说明

        保持鼓励：对于孩子的任何回应，哪怕是简单的重复，都要给予积极反馈，建立他们的信心。
        灵活调整：如果孩子不回应，可以尝试换一个话题或方式。
        注重进步：每一步都建立在上一阶段的基础上，目标是让互动轻松愉快并有成效。

    根据上述场景进行练习，逐步提高与孤独症儿童沟通的能力。"""
    print("begin conversation:")
    mem1="""

    以下是正在进行的对话：
        你现在扮演一个水果店老板，孤独症儿童走进店里
        打个招呼吧"""

    systemprompt = info+example+prompt
    conversation_history.insert(0, {"role": "system", "content":systemprompt})
    #chat_with_openai(mem1)
    #print(conversation_history)


    import asyncio
    asyncio.run(async_chat_with_openai(mem1))

    print(conversation_history)


    """
    while True:
        user_message = input("user:")
        #print("user: ", user_message)
        assistant_reply = chat_with_openai(user_message)
        ##print("assistant:", assistant_reply)
    """
    """
    user_message = "I am Terry"
    print("user: ", user_message)
    assistant_reply = chat_with_openai(user_message)
    print("assistant:", assistant_reply)

    # 继续对话
    user_message = "Who am I?"
    print("user: ", user_message)
    assistant_reply = chat_with_openai(user_message)
    print("assistant:", assistant_reply)
    """
