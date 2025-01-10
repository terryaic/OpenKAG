import os
from mem0 import Memory

os.environ["OPENAI_API_KEY"] = "xxx"
os.environ["OPENAI_BASE_URL"]= "http://localhost:8097/v1"

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "qwen2-instruct-70b",
            "temperature": 0.2,
            "max_tokens": 1500,
        }
    },
    "embedder":{
        "provider": "openai",
        "config":{
            "model": "bge-large-zh-v1.5"
        }
    },
    "history_db_path": "/home/terry/.mem0/history.db",
    "collection_name": "mem0", 
    "embedding_model_dims": 1024
}

xconfig = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gemma2:27b",
            "temperature": 0.2,
            "max_tokens": 1500,
        }
    },
    "embedder":{
        "provider": "openai",
        "config":{
            "model": "nomic-embed-text"
        }
    },
    "history_db_path": "/home/terry/.mem0/history.db",
    "collection_name": "mem0", 
    "embedding_model_dims": 1024
}



# Initialize Mem0
m = Memory.from_config(config)

class Mem0DB():
    def __init__(self, dir=None):
        if dir is not None:
            self.build_knowledge_base(dir)
        
    def build_knowledge_base(self, directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and (file_path.endswith('.txt') or file_path.endswith(".md")):
                self.add_document(file_path, 'default')

    def add_document(self, file_path, user_id):
        print("adding document:" + file_path)
        with open(file_path, 'r') as fp:
            content = fp.read()
        m.add(content, user_id)

    def dump(self):
        return m.get_all()

def search_db(text, user_id='default'):

    # Search memories
    related_memories = m.search(query=text, user_id=user_id)
    print(related_memories)
    return None


def update_db(data, user_id):
    memory_id = related_memories[0]["id"]

    # Update a memory
    result = m.update(memory_id=memory_id, data="Likes to play tennis on weekends")
    print(result)

    # Get memory history
    history = m.history(memory_id=memory_id)
    print(history)

if __name__ == "__main__":
    import sys
    mem0db = Mem0DB("test")
    print("searching...")
    ret = search_db(sys.argv[1])
    print(ret)
    print(mem0db.dump())