import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.core.service_context import ServiceContext,set_global_service_context
from llama_index.core.llms import ChatMessage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.milvus import MilvusVectorStore
from settings import get_llm_model, get_llm_base_url, API_KEY
from settings import MAX_INPUT_TOKEN, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, MAX_TOKENS,RAG_EMBEDDING_MODEL,EMBEDDING_DIM
from settings import GRAPHRAG_EMBEDDING_MODEL,GRAPHRAG_EMBEDDING_API_BASE_URL,GRAPHRAG_EMBEDDING_API_KEY,RAG_LOCAL_EMBEDDING
from settings import FILE_EXTS
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time


llm = OpenAILike(model=get_llm_model(), api_base=get_llm_base_url(), api_key=API_KEY, max_tokens=MAX_TOKENS, context_window=MAX_INPUT_TOKEN)

if RAG_LOCAL_EMBEDDING:
    embed_model = HuggingFaceEmbedding(
        model_name=RAG_EMBEDDING_MODEL
    )
else:
    #from aicembeddings import AICEmbedding
    embed_model = OpenAIEmbedding(
        model_name=GRAPHRAG_EMBEDDING_MODEL,
        api_key=GRAPHRAG_EMBEDDING_API_KEY,
        api_base=GRAPHRAG_EMBEDDING_API_BASE_URL
    )

Settings.llm = llm
Settings.embed_model = embed_model
Settings.node_parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
Settings.num_output = EMBEDDING_DIM
Settings.context_window = MAX_INPUT_TOKEN

from llama_index.core import ChatPromptTemplate

DEFAULT_QA_PROMPT_STR = (
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Given the context information and not prior knowledge, "
    "answer the question: {query_str}\n"
)

def get_qa_template(qa_prompt_str=None):
  # Text QA Prompt
  if qa_prompt_str is None:
      qa_prompt_str = DEFAULT_QA_PROMPT_STR
  chat_text_qa_msgs = [
    (
        "system",
        "Always answer the question, even if the context isn't helpful.",
    ),
    ("user", qa_prompt_str),
  ]
  text_qa_template = ChatPromptTemplate.from_messages(chat_text_qa_msgs)
  return text_qa_template

def get_advanced_qa_template(system_prompt, qa_prompt_str=None, chat_history=[]):
  if qa_prompt_str is None:
      qa_prompt_str = DEFAULT_QA_PROMPT_STR
  chat_text_qa_msgs = [
    (
        "system",
        system_prompt
    )]
  for chat in chat_history:
      chat = (chat[0], chat[1].replace("{","(").replace("}",")"))
      chat_text_qa_msgs.append(chat)
  chat_text_qa_msgs.append(
    ("user", qa_prompt_str)
  ) 
  text_qa_template = ChatPromptTemplate.from_messages(chat_text_qa_msgs)
  return text_qa_template

class BaseRAG():
    def __init__(self):
        self.top_k = TOP_K

    async def init(self, db_uri, dir, storage_dir, prompt=None):
        self.last_active_time = time.time()
        self._db_uri = db_uri
        """if os.path.exists(db_uri):
            vector_store = MilvusVectorStore(uri=db_uri, overwrite=False)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
        else:
            vector_store = MilvusVectorStore(uri=db_uri, dim=EMBEDDING_DIM, overwrite=True)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)"""
        self.storage_dir = storage_dir

        async def build_docs(that, dir, storage_dir):
            if os.path.exists(storage_dir):
                storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
                index = load_index_from_storage(storage_context=storage_context)
            else:
                files = os.listdir(dir)
                if len(files) > 0:
                    documents = SimpleDirectoryReader(dir, required_exts=FILE_EXTS).load_data()
                else:
                    documents = []
                print(f'doc len:{len(documents)}')
                index = VectorStoreIndex.from_documents(documents)#, storage_context=storage_context)
                index.storage_context.persist(storage_dir)
            that.index = index
        try:
          loop = asyncio.get_event_loop()
          with ThreadPoolExecutor() as executor:
            task = loop.run_in_executor(executor, build_docs, self, dir, storage_dir)
            await asyncio.gather(task, return_exceptions=True)
        except Exception as e:
          print(e)
          task = asyncio.create_task(build_docs(self, dir, storage_dir))
          await task

        self._text_qa_template = get_qa_template(prompt)
        self.query_engine = self.index.as_query_engine(
                        streaming=True,
                        text_qa_template=self._text_qa_template,
                        similarity_top_k = self.top_k)
        self.chat_engine = self.index.as_chat_engine(
                        chat_mode="condense_plus_context",
                        streaming=True,
                        text_qa_template=self._text_qa_template,
                        similarity_top_k = self.top_k
                    )
        
    async def build_knowledge_base(self, directory):
        self.last_active_time = time.time()
        """vector_store = MilvusVectorStore(uri=self._db_uri, dim=EMBEDDING_DIM, overwrite=True)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)"""
        def build_docs(that, directory):
            documents = SimpleDirectoryReader(directory).load_data()
            that.index = VectorStoreIndex.from_documents(documents)#,storage_context = storage_context)
            that.index.storage_context.persist(self.storage_dir)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            task = loop.run_in_executor(executor, build_docs, self, directory)
            await asyncio.gather(task, return_exceptions=True)
        
        self.query_engine = self.index.as_query_engine(
                        streaming=True,
                        text_qa_template=self._text_qa_template,
                        similarity_top_k = self.top_k)
        #self.index.insert_nodes(documents)

    async def add_document(self, file_path):
        self.last_active_time = time.time()
        def add_doc(index, file_path):
            documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            for document in documents:
                index.insert(document)
            index.storage_context.persist(self.storage_dir)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            task = loop.run_in_executor(executor, add_doc, self.index, file_path)
            await asyncio.gather(task, return_exceptions=True)

    def get_chat_engine(self):
        return self.index.as_chat_engine(
                        chat_mode="condense_plus_context",
                        streaming=True,
                        similarity_top_k = self.top_k,
                        verbose=True
                    )
    
    def retrieve(self, query):
        from llama_index.core.retrievers import VectorIndexRetriever
        retriever = VectorIndexRetriever(
            self.index,
            #filters=MetadataFilters(filters=exact_match_filters),
            top_k=TOP_K,
        )
        results = retriever.retrieve(query)
        return results
    
    def close(self):
        if hasattr(self.index, "storage_context"):
            vector_store = self.index.storage_context.vector_store
            print("release storage")
        else:
            vector_store = self.index.vector_store
            print("release vector store")
        if hasattr(vector_store, 'clear'):
            vector_store.clear()
        if hasattr(vector_store, 'close'):
            vector_store.close()
        del vector_store
        del self.index
