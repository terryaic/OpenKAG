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

from settings import TOP_K

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().handlers = []
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from llamaindex import BaseRAG,llm
from llama_index.core.llms import ChatMessage
from settings import RAG_USING_RERANK, RAG_RERANK_MODEL

class AdvancedRAG(BaseRAG):
    def __init__(self, db_uri, dir, prompt=None):
        # global variables used later in code after initialization
        self.retriever = None
        self.reranker = None
        self.query_engine = None

        super().__init__(db_uri, dir, prompt=prompt)
        if RAG_USING_RERANK:
            self.bootstrap()

    def bootstrap(self):
        # We can pass in the index, doctore, or list of nodes to create the retriever
        #self.retriever = BM25Retriever.from_defaults(similarity_top_k=2, index=self.index)
        self.retriever = self.index.as_retriever()
        self.retriever.k = 5

        # reranker setup & initialization
        self.reranker = SentenceTransformerRerank(top_n=3, model=RAG_RERANK_MODEL)

        self.query_engine = RetrieverQueryEngine.from_args(
            retriever=self.retriever,
            node_postprocessors=[self.reranker],
            #service_context=self.service_context,
            service_context=Settings,
            use_async=True,
            streaming=True
        )

    def query(self, query):
        # will retrieve context from specific companies
        """
        nodes = self.retriever.retrieve(query)
        reranked_nodes = self.reranker.postprocess_nodes(
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
    
    def get_query_engine(self, top_k=TOP_K):
        self.last_active_time = time.time()
        if self.retriever:
            self.query_engine = RetrieverQueryEngine.from_args(
                retriever=self.retriever,
                node_postprocessors=[self.reranker],
                #service_context=self.service_context,
                service_context=Settings,
                use_async=True,
                streaming=True
            )
        else:
            self.query_engine = self.index.as_query_engine(
                            streaming=True,
                            text_qa_template=self._text_qa_template,
                            similarity_top_k = self.top_k)
        return self.query_engine

stop_chat = False
async def stream_chat(text, send_text):
    global stop_chat
    stop_chat = False
    message = [ChatMessage(content=text, role="user")]
    async for x in await llm.astream_chat(message):
        if stop_chat:
            break
        #ret = x.raw['choices'][0].text
        ret = x.raw.choices[0].text
        await send_text(ret)
    return stop_chat

async def stream_chat_in_context(messages, send_text):
    global stop_chat
    stop_chat = False
    message = [ChatMessage(content=m['text'], role=m["role"]) for m in messages]
    async for x in await llm.astream_chat(message):
        if stop_chat:
            break
        #ret = x.raw['choices'][0].text
        ret = x.raw.choices[0].text
        await send_text(ret)
    return stop_chat

async def stream_complete(text, send_text):
    async for x in await llm.astream_complete(text):
        #ret = x.text
        ret = x.raw['choices'][0].text 
        await send_text(ret)

def stop_streaming():
    global stop_chat
    stop_chat = True

async def kdb_chat(query_engine, text, send_text):
    global stop_chat
    stop_chat = False
    response = await query_engine.astream_chat(text)
    async for token in response.async_response_gen():
        if stop_chat:
            break
        await send_text(token)
    return stop_chat


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

async def kdb_query(query_engine, text, send_text):
    global stop_chat
    stop_chat = False
    response = await query_engine.aquery(text)
    query_engine._source_nodes = response.source_nodes
    async for token in response.async_response_gen():
        if stop_chat:
            break
        await send_text(token)
    return stop_chat

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

    
