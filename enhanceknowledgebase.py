from sentence_transformers import SentenceTransformer
import os
import logging
from backend.utils import split_text
from settings import get_llm_model_local

def debug(chunks):
    for i, chunk in enumerate(chunks):
        print(f'index:{i}, text:{chunk}')

# 假设函数，用于模拟 matt_solomatov_toolkit 的文本处理
def process_text_with_matt_solomatov_toolkit(text):
    return split_text(text,get_llm_model_local())

    from mattsollamatools import chunker
    # 这里简单地将文本分割为句子作为示例
    #return text.split('. ')
    chunks = chunker(text)
    debug(chunks)
    return chunks

class EnhancedKnowledgeBase:
    def __init__(self, directory, model_name='./models/sentence-transformers_all-MiniLM-L6-v2'):
        self.directory = directory
        self.model = SentenceTransformer(model_name)
        self.knowledge_base = {}
        self.vectorized_knowledge = []

    def build_knowledge_base(self, directory):
        self.knowledge_base = {}
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            ext_name = filename.split(".")[-1]
            if os.path.isfile(file_path):
                if ext_name in ['txt','py']:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        chunks = process_text_with_matt_solomatov_toolkit(content)
                        self.knowledge_base[filename] = chunks
                if ext_name == 'csv':
                    with open(file_path, 'r', encoding='utf-8') as file:
                        chunks = file.readlines()
                        self.knowledge_base[filename] = chunks
        self.vectorize_knowledge_base()

    def vectorize_knowledge_base(self):
        self.vectorized_knowledge = []
        for filename, chunks in self.knowledge_base.items():
            article={}
            article['embeddings'] = []
            article['url'] = filename
            embeddings = self.model.encode(chunks)
            for (chunk, embedding) in zip(chunks, embeddings):
                item = {}
                item['source'] = chunk
                item['embedding'] = embedding.tolist()  # Convert NumPy array to list
                item['sourcelength'] = len(chunk)
                article['embeddings'].append(item)
            self.vectorized_knowledge.append(article)

    def get_vectorized_content(self, filename):
        ret = None
        index = 0
        for vec in self.vectorized_knowledge:
            if vec['url'] == filename:
                ret = vec
                break
        return ret

    def list_files(self):
        return list(self.knowledge_base.keys())
    
    def query(self, question):
        import time
        from search import knn_search
        # Embed the user's question
        t1 = time.time()
        question_embedding = self.model.encode([question])
        t2 = time.time()
        print(f'encode:{t2-t1}')

        # Perform KNN search to find the best matches (indices and source text)
        best_matches = knn_search(question_embedding, self.vectorized_knowledge, k=5)
        t3 = time.time()
        print(f'knn_search:{t3-t2}')
        return best_matches

if __name__  == "__main__":
    # 使用方法
    directory_path = "data"
    enhanced_kb = EnhancedKnowledgeBase(directory_path)
    enhanced_kb.build_knowledge_base()
    enhanced_kb.vectorize_knowledge_base()

    # 获取特定文件的向量化内容
    print(enhanced_kb.get_vectorized_content("example.txt"))

    # 列出知识库中的所有文件
    print(enhanced_kb.list_files())
