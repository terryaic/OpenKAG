import os

class KnowledgeBaseBuilder:
    def __init__(self, directory):
        self.directory = directory
        self.knowledge_base = {}

    def build_knowledge_base(self):
        for filename in os.listdir(self.directory):
            file_path = os.path.join(self.directory, filename)
            if os.path.isfile(file_path) and file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.knowledge_base[filename] = file.read()

    def get_file_content(self, filename):
        return self.knowledge_base.get(filename, "File not found in knowledge base.")

    def list_files(self):
        return list(self.knowledge_base.keys())
