import asyncio
import functools
from typing import Optional, Union, Callable

import autogen
import os
from autogen import register_function, ConversableAgent, ChatResult
#from function import get_weather,  getinput, install_callback, bingsearch
from .function import get_weather, getinput, install_callback, bingsearch_answer, sum_model_api, set_callback
from autogen.cache import Cache, AbstractCache
from .init import  config_list_path
#封装ChatBotSystem类11

class ChatBotSystem:
    def __init__(self, session_id, send_cb, config_file=config_list_path):
        # Load configuration
        self.config_list = autogen.config_list_from_json(env_or_file=config_file)

        print("configlist", self.config_list)
        # Initialize agents
        self.initialize_agents()
        #self.setup_group_chat()
        print("Setting up group chat...")
        print("Initializing manager...")
        #self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config={"config_list": self.config_list})
        print("Registering functions...")
        print("我的sessionid是", session_id)
        self._session_id = session_id
        print("我的callback是", send_cb)
        self._send_text_cb = send_cb
        self.register_functions()
        self.prompt=self.planner.get_stored_prompt()
        print("sssssssssss",self.prompt)

        self.manager = None  # 将 manager 的初始化推迟到每次创建 GroupChat 时
        set_callback(send_cb)

    def initialize_agents(self):
        # Define PlannerAgent with custom methods
        class PlannerAgent(autogen.AssistantAgent):
            def __init__(self, name, system_message,llm_config,is_termination_msg=None,):
                super().__init__(name, system_message,llm_config, )
                self._stored_prompt = ''
                self.websocket = None  # 初始化 websocket 属性

            async def call_tool(self, *args, **kwargs):
                tool_name = kwargs.get('tool_name', '')
                if tool_name == 'getinput':
                    self.websocket = kwargs.get('websocket', None)
                    self._stored_prompt = kwargs.get('prompt', '')+ '\n'
                return await super().call_tool(*args, **kwargs)

            def get_stored_prompt(self):
                return self._stored_prompt

            async def getinput(self, prompt: str) -> str:
                """异步获取用户输入."""
                print("正在获取用户输入")
                global g_callback
                # 使用回调函数发送提示
                if g_callback:
                    response = await asyncio.to_thread(g_callback, prompt)
                    return response

                return ""

        class CustomUserProxyAgent(autogen.UserProxyAgent):
            def __init__(self, name, system_message, llm_config, is_termination_msg=None,
                         default_auto_reply="", code_execution_config=False,
                          human_input_mode="ALWAYS", **kwargs):
                super().__init__(name, system_message, llm_config,
                                 default_auto_reply=default_auto_reply,
                                 code_execution_config=code_execution_config,
                                 human_input_mode=human_input_mode, **kwargs)
                self.first_input = True
            async def a_get_human_input(self, prompt: str) -> str:
                print(" a_get_human_input成功调用")
                """Override to customize the async way to get human input."""
                print(self.first_input)
                if self.first_input:
                    self.first_input = False
                    print(self.first_input )
                    loop = asyncio.get_running_loop()
                    reply = await loop.run_in_executor(None, functools.partial(self.get_human_input, prompt))
                    return reply
                return "continue,if finisher end with 'TERMINATE' ,"  # 之后返回自动回复

        # Create instances of agents
        self.user_proxy =CustomUserProxyAgent(
            name="user_proxy",
            llm_config={"config_list": self.config_list},
            is_termination_msg=lambda x: x.get("content", "") is not None and "terminate" in x["content"].lower(),
            #"You are the human admin. Interact with the planner for task approvals; do not execute tasks directly.
            system_message="You are the human admin. Interact with the planner for task approvals; do not execute tasks directly. ",
            default_auto_reply="continue.",
            code_execution_config=False,
        )

        self.scraper_agent = autogen.AssistantAgent(
            name="scraper",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get("content", "") is not None and "terminate" in x["content"].lower(),
            llm_config={"config_list": self.config_list},
            system_message="You are an AI assistant capable of scraping web pages.Retain all crawl information，不要使用现有的知识回答，搜索优先。如果工具返回信息足够回答用户问题，你来回答.如果现有的信息无法回答问题，请继续联网搜索，不要询问用户.如果已有信息能回答问题就终止聊天.ending with 'TERMINATE'."
        )

        self.Sum = autogen.AssistantAgent(
            name="Sum",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get("content", "") is not None and "terminate" in x["content"].lower(),
            llm_config={"config_list": self.config_list},
            system_message="If the information is cluttered, summarize it concisely to answer the user's questions.Please keep the url and title of the information the chat_results，ending with 'TERMINATE'.",

        )

        self.weather_agent = autogen.AssistantAgent(
            name="weather",
            is_termination_msg=lambda x: x.get("content", "") is not None and "terminate" in x["content"].lower(),
            llm_config={"config_list": self.config_list},
            system_message= "Act as a weather expert. Check the weather only if an address is provided. If not, consult the planner first. Always end with 'TERMINATE'.",

            #system_message="Act as a weather delegate. If no location is available, consult the planner first. Dont' make up anything. Always end your response with 'TERMINATE'."
        )

        self.planner = PlannerAgent(
            name="Planner",
            is_termination_msg=lambda x: x.get("content", "") is not None and "terminate" in x["content"].lower(),
            #system_message="Guide agents using user input. Don't make up anything, if you have question or ambiguity, ask user to input. Do not repeatedly ask for the same information. Use tools for necessary details, ending with 'TERMINATE'.",
            system_message="Guide agents based on user input .Do not answer directly or fabricate addresses.不要使用现有的知识回答，搜索优先。Use tools for necessary input and conclude with 'TERMINATE'.",
            llm_config={"config_list": self.config_list,},
        )

    def setup_group_chat(self):
        # Set up group chat
        self.groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.planner, self.scraper_agent, self.weather_agent],
            messages=[],
            max_round=50
        )
    def create_group_chat(self):
        # Create a new group chat for a user
        groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.planner, self.scraper_agent, self.weather_agent],
            messages=[],
            max_round=10
        )
        self.manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={"config_list": self.config_list})
        return groupchat
    def register_functions(self):
        # Register functions
        print("开始注册")
        # register_function(
        #     sum_model_api,
        #     caller=self.planner,
        #     executor=self.planner,
        #     name="sum_model_api",
        #     description="sum_model_api"
        # )

        register_function(
            getinput,
            caller=self.planner,
            executor=self.planner,
            name="getinput",
            description="Request user input for a query."
        )
        print("getinput已注册")
        register_function(
            get_weather,
            caller=self.planner,
            executor=self.weather_agent,
            name="get_weather",
            description="Fetch weather data for the given city."
        )
        print("get_weather已注册")
        register_function(
            bingsearch_answer,
            caller=self.planner,
            executor=self.scraper_agent,
            name="bingsearch",
            description="Scrape text based on the given query. with the session id :" + self._session_id
        )
        print("get_scraped_contents已注册")
    # def initiate_chat(self, message):
    #     # Initialize chat with the user proxy
    #     self.user_proxy.initiate_chat(
    #         self.manager,
    #         message=message
    #     )
    async def initiate_chat(self,message):
        self.user_proxy.first_input = False
        from datetime import datetime
        now = datetime.now().strftime("当前时间是：%Y年%m月%d日%H时")
        message_with_time = f"{now}: {message}"
        with Cache.disk() as cache:
            chatresult= await self.user_proxy.a_initiate_chat(  # noqa: F704
                self.manager,
                message=message_with_time,
                cache=cache,
                summary_method="reflection_with_llm",
                summary_args={
                    "summary_prompt": """将获取内容进行总结，并按照以下格式进行格式化,输出markdown的格式：
            ---
            *海风*：
            `用户问题的答案，或者网上爬取资料的总结`
            
            ---

            """
                },
                )
        return chatresult.summary
def callback(prompt):
    return input()

# Example usage
if __name__ == "__main__":
    install_callback(callback)
    chatbot_system = ChatBotSystem()
    asyncio.run(chatbot_system.initiate_chat("今天天气怎么样"))