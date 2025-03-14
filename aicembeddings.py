from llama_index.core.embeddings import BaseEmbedding
import requests
from typing import List

class AICEmbedding(BaseEmbedding):
    api_key: str = Field(description="The OpenAI API key.")
    model_name: str = Field(description="The OpenAI model.")
    api_base: str= Field(description="The OpenAI API url.")
    def __init__(self, model_name: str = "", api_key: str="", api_base: str=""):
        super().__init__()
        self.model_name = model_name
        self.api_url = api_base
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = requests.post(self.api_url, headers=self.headers, json={"inputs": texts})
        return response.json()

    # Required implementations
    def _get_text_embedding(self, text: str) -> List[float]:
        """Embed a single text"""
        return self._get_text_embeddings([text])[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts"""
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        return response.json()

    def _get_query_embedding(self, query: str) -> List[float]:
        """Embed a query (can be same as text embedding)"""
        return self._get_text_embedding(query)

    # Async implementations (can mirror sync versions if not using async)
    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)
