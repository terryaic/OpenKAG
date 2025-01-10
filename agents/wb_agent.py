import asyncio
import json
from datetime import datetime
from typing import Dict, Any



from .function import install_callback


#fastapi运行服务器
#https://api.deepseek.com/v1



class initagent:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.chatbot_systems = {}
        self.conversation_status: Dict[str, bool] = {"default": False} # 对话是否结束

    async def send_prompt_to_client_and_wait(self, text_cb, prompt: str):
        print("sending")
        message = json.dumps({"message": "请提供额外输入。", "prompt": prompt})
        print("发送的消息", message)
        try:
            return await text_cb(prompt)
        except Exception as e:
            print(f"发送消息时发生异常: {e}")
            return None

    async def initiate_conversation(self, text_cb, session_id: str):
        print("正在初始化聊天")
        self.conversation_status[session_id] = False  # 设置对话开始为未结束
        print("self.conversation_status[session_id]",self.conversation_status[session_id])
        async def callback(prompt):
            print("callback成功调用")
            a = await self.send_prompt_to_client_and_wait(text_cb, prompt)

            return a

        install_callback(callback)
        print(self.sessions)
        user_message = self.sessions[session_id].get("message", "")
        print("用户输入的问题是:", user_message)

        if user_message:
            chatbot_system = self.chatbot_systems[session_id]
            chatbot_system.create_group_chat()
            chatresult = await chatbot_system.initiate_chat(user_message)
            #res = json.dumps({"chatresult": chatresult})
            print(type(chatresult))
            print("chat res is "+chatresult)
            self.conversation_status[session_id] = True
            return chatresult



