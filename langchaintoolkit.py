
from langchain_community.vectorstores import DocArrayInMemorySearch, FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings,LlamaCppEmbeddings
from langchain_community.document_loaders import TextLoader,CSVLoader
from langchain.text_splitter import CharacterTextSplitter
import threading
import os


""""
from langchain.indexes import VectorstoreIndexCreator
retriever = db.as_retriever()
index = VectorstoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch, embedding=embeddings
).from_loaders([loader])
"""
model_name = './models/sentence-transformers_all-MiniLM-L6-v2'
class MemoryVectore:
    def __init__(self, directory):
        self.directory = directory
        self._embeddings = HuggingFaceEmbeddings(model_name=model_name)#LlamaCppEmbeddings(model_path="../openbuddy-zephyr-7b-v14.1/ggml-model-f16.gguf")
        self._text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

        #self._db = DocArrayInMemorySearch.from_documents(
        #    [], 
        #    self._embeddings
        #)
        docs = TextLoader(file_path="data/default.txt", encoding='utf-8').load()
        self._db = FAISS.from_documents(docs, self._embeddings)

    def build_knowledge_base(self, directory, chunk_size=1000):
        docs = TextLoader(file_path="data/default.txt", encoding='utf-8').load()
        self._db = FAISS.from_documents(docs, self._embeddings)
        def build_thread(that: MemoryVectore, directory):
            text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                print(f'loading:{file_path}')
                ext_name = filename.split(".")[-1]
                if os.path.isfile(file_path):
                    if ext_name in ['txt']:
                        loader = TextLoader(file_path=file_path, encoding='utf-8')
                        raw_documents = loader.load()
                        docs = text_splitter.split_documents(raw_documents)
                        that._db.add_documents(docs)
                    elif ext_name in ['csv']:
                        loader = CSVLoader(file_path=file_path, encoding='utf-8')
                        raw_documents = loader.load()
                        that._db.add_documents(raw_documents)
                    elif ext_name in ['py']:
                        loader = TextLoader(file_path=file_path, encoding='utf-8')
                        raw_documents = loader.load()
                        #print(raw_documents)
                        that._db.add_documents(raw_documents)
            that._db.save_local(that.directory)
            print("build knowledge finished!")
        t1 = threading.Thread(target=build_thread, args=(self,directory,))
        t1.start()

    def query(self, text):
        docs = self._db.similarity_search(text)
        return docs
    
    def add_document(self, file_path):
        print(f'loading:{file_path}')
        ext_name = file_path.split(".")[-1]
        if os.path.isfile(file_path) and ext_name in ['txt','py']:
            loader = TextLoader(file_path=file_path, encoding='utf-8')
            raw_documents = loader.load()
            docs = self._text_splitter.split_documents(raw_documents)
            self._db.add_documents(docs)
            self._db.save_local(self.directory)

    def load_from_file(self, index = 'index'):
        file_path = os.path.join(self.directory, f'{index}.faiss')
        if os.path.exists(file_path):
            print(f'loading:{index}')
            self._db = FAISS.load_local(self.directory, embeddings=self._embeddings, index_name = index)

    def save_to_file(self, index = 'index'):
        self._db.save_local(self.directory, index_name=index)

    def build_all(self, directory, ext=None, prefix=None):
        docs = TextLoader(file_path="data/default.txt", encoding='utf-8').load()
        self._db = FAISS.from_documents(docs, self._embeddings)
        def build_thread(that: MemoryVectore, directory):
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    #print(filename)
                    file_path = os.path.join(root, filename)
                    if ext is not None and not filename.endswith(ext):
                        continue
                    if prefix is not None and not filename.startswith(prefix):
                        continue
                    print(f'loading:{file_path}')
                    loader = TextLoader(file_path=file_path, encoding='utf-8')
                    raw_documents = loader.load()
                    docs = that._text_splitter.split_documents(raw_documents)
                    that._db.add_documents(docs)
            #that._db.save_local(that.directory)
        build_thread(self, directory)
        print("build knowledge finished!")

if __name__ =="__main__":
    import sys
    mm = MemoryVectore(sys.argv[1])
    mm.build_knowledge_base(sys.argv[2])
    docs = mm.query(sys.argv[3])
    print(docs)
