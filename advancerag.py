#import nest_asyncio
import os
import sys
import time
import logging
#from dotenv import load_dotenv, find_dotenv
from llama_index.core.query_engine import RetrieverQueryEngine
#from llama_index.retrievers.bm25.base import BM25Retriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core import QueryBundle
from llama_index.core import Settings

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().handlers = []
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

import llamaindex
from llamaindex import BaseRAG,llm
from llama_index.core.llms import ChatMessage
from settings import TOP_K, RAG_RERANK_TOP_K, RAG_USING_RERANK, RAG_RERANK_MODEL
if RAG_USING_RERANK:
        reranker = SentenceTransformerRerank(top_n=TOP_K, model=RAG_RERANK_MODEL)

class AdvancedRAG(BaseRAG):
    def __init__(self):
        super().__init__()
        if RAG_USING_RERANK:
            self.top_k = RAG_RERANK_TOP_K

    async def init(self, db_uri, dir, storage_dir, prompt=None):
        # global variables used later in code after initialization
        self.retriever = None
        self.query_engine = None

        await super().init(db_uri, dir, storage_dir, prompt=prompt)
        if RAG_USING_RERANK:
            self.bootstrap()

    def bootstrap(self):
        # We can pass in the index, doctore, or list of nodes to create the retriever
        #self.retriever = BM25Retriever.from_defaults(similarity_top_k=self.top_k, index=self.index)
        self.retriever = self.index.as_retriever(similarity_top_k=self.top_k)
        self.retriever.k = RAG_RERANK_TOP_K

        # reranker setup & initialization

        self.query_engine = RetrieverQueryEngine.from_args(
            retriever=self.retriever,
            node_postprocessors=[reranker],
            #service_context=self.service_context,
            service_context=Settings,
            use_async=True,
            streaming=True
        )

    def query(self, query):
        # will retrieve context from specific companies
        """
        nodes = self.retriever.retrieve(query)
        reranked_nodes = reranker.postprocess_nodes(
            nodes,
            query_bundle=QueryBundle(query_str=query)
        )

        print("Initial retrieval: ", len(nodes), " nodes")
        print("Re-ranked retrieval: ", len(reranked_nodes), " nodes")

        for node in nodes:
            print(node)

        for node in reranked_nodes:
            print(node)
        """
        response = self.query_engine.query(str_or_query_bundle=query)
        return response
    
    async def aquery(self, query):
        response = await self.query_engine.aquery(str_or_query_bundle=query)
        print(response)
        return response
    
    def get_query_engine(self, system_prompt=None, qa_prompt_str=None, chat_history=[]):
        self.last_active_time = time.time()
        if system_prompt:
            text_qa_template = llamaindex.get_advanced_qa_template(system_prompt, qa_prompt_str, chat_history)
        else:
            text_qa_template = self._text_qa_template
        if self.retriever:
            self.query_engine = RetrieverQueryEngine.from_args(
                retriever=self.retriever,
                node_postprocessors=[reranker],
                #service_context=self.service_context,
                service_context=Settings,
                use_async=True,
                streaming=True,
                text_qa_template=text_qa_template
            )
        else:
            self.query_engine = self.index.as_query_engine(
                            streaming=True,
                            text_qa_template=text_qa_template,
                            similarity_top_k = self.top_k)
        return self.query_engine
    
    def get_node_context(self, node_id):
        # 获取存储上下文
        storage_context = self.index.storage_context
        # 获取全部节点
        all_nodes = storage_context.docstore.to_dict()
        context = all_nodes["docstore/data"].get(node_id)["__data__"]["text"]
        return context
    
    async def kdb_query(self, text, callback):
        self.stop_chat = False
        response = await self.query_engine.aquery(text)
        self.query_engine._source_nodes = response.source_nodes
        async for token in response.async_response_gen():
            if self.stop_chat:
                break
            await callback(token)
        return self.stop_chat

class ChatSession:
    def __init__(self, user=None):
        self.stop_chat = False
        self.user = user

async def stream_chat(text, send_text, session: ChatSession):
    message = [ChatMessage(content=text, role="user")]
    async for x in await llm.astream_chat(message):
        if session.stop_chat:
            break
        #ret = x.raw['choices'][0].text
        ret = x.raw.choices[0].text
        await send_text(ret)
    return session.stop_chat

async def stream_chat_in_context(messages, send_text, session: ChatSession):
    message = [ChatMessage(content=m['text'], role=m["role"]) for m in messages]
    async for x in await llm.astream_chat(message):
        if session.stop_chat:
            break
        #ret = x.raw['choices'][0].text
        ret = x.raw.choices[0].text
        await send_text(ret)
    return session.stop_chat

async def stream_complete(text, send_text):
    async for x in await llm.astream_complete(text):
        #ret = x.text
        ret = x.raw['choices'][0].text 
        await send_text(ret)

def stop_streaming(session: ChatSession=None):
    if session:
        session.stop_chat = True

async def kdb_chat(query_engine, text, send_text, session: ChatSession):
    response = await query_engine.astream_chat(text)
    async for token in response.async_response_gen():
        if session.stop_chat:
            break
        await send_text(token)
    return session.stop_chat

async def chat(text):
    system_msg = ChatMessage(content="you are a ai assitant, you can answer question based on the user input, answer in Chinese", role="system")
    message = [system_msg, ChatMessage(content=text, role="user")]
    x = llm.chat(message)
    print(x)
    ret = x.raw.choices[0].text
    return ret

async def achat(text):
    system_msg = ChatMessage(content="you are a ai assitant, you can answer question based on the user input, answer in Chinese", role="system")
    message = [system_msg, ChatMessage(content=text, role="user")]
    x = await llm.achat(message)
    print(x)
    ret = x.raw.choices[0].text
    return ret

async def kdb_query(query_engine, text, send_text, session: ChatSession):
    response = await query_engine.aquery(text)
    query_engine._source_nodes = response.source_nodes
    async for token in response.async_response_gen():
        if session.stop_chat:
            break
        await send_text(token)
    return session.stop_chat

async def kdb_query_nc(query_engine, text):
    response = await query_engine.aquery(text)  # 获取完整的响应
    query_engine._source_nodes = response.source_nodes
    
    # 通过异步生成器获取所有 tokens
    result_tokens = []
    async for token in response.async_response_gen():
        result_tokens.append(token)  # 将每个 token 存储起来
    
    # 将所有 token 合并成一个完整的字符串
    full_response = ''.join(result_tokens)
    
    return full_response, False


if __name__ == "__main__":
    import asyncio
    import time
    adv_rag = AdvancedRAG("./doctest")
    """
    resp = adv_rag.query("专业图卡与消费显卡的区别?")
    print(resp)
    """
    answer = ''
    def send_text(text):
        answer.append(text)
    asyncio.ensure_future(adv_rag.achat("专业图卡与消费显卡的区别?", send_text))
    print(answer)
    asyncio.ensure_future(adv_rag.aquery("专业图卡与消费显卡的区别?"))

    
