from transformers import AutoTokenizer, AutoModel
import numpy as np
import torch
from knowledgebase import KnowledgeBaseBuilder

class VectorizedKnowledgeBase(KnowledgeBaseBuilder):
    def __init__(self, directory, model_name='bert-base-uncased'):
        super().__init__(directory)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.vectorized_knowledge = {}

    def build_vectorized_knowledge_base(self):
        self.build_knowledge_base()
        for filename, content in self.knowledge_base.items():
            inputs = self.tokenizer(content, return_tensors='pt', truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            self.vectorized_knowledge[filename] = outputs.last_hidden_state.mean(dim=1).numpy()

    def find_similar(self, query_text, top_n=3):
        query_inputs = self.tokenizer(query_text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            query_outputs = self.model(**query_inputs)
        query_vector = query_outputs.last_hidden_state.mean(dim=1).numpy()

        similarity_scores = {}
        for filename, vec in self.vectorized_knowledge.items():
            cos_sim = np.dot(vec, query_vector.T) / (np.linalg.norm(vec) * np.linalg.norm(query_vector))
            similarity_scores[filename] = cos_sim.item()

        sorted_files = sorted(similarity_scores, key=similarity_scores.get, reverse=True)
        return [(file, similarity_scores[file]) for file in sorted_files[:top_n]]

if __name__  == "__main__":
    # 使用方法
    directory_path = "/path/to/your/directory"
    vectorized_kb = VectorizedKnowledgeBase(directory_path)
    vectorized_kb.build_vectorized_knowledge_base()

    # 查询相似文档
    query = "Your query text here"
    print(vectorized_kb.find_similar(query))
