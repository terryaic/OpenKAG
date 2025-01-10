from sentence_transformers import SentenceTransformer
import requests
import json
import time
from search import knn_search
from enhanceknowledgebase import EnhancedKnowledgeBase
from settings import get_llm_url

directory_path = "uploaded_files"
enhanced_kb = EnhancedKnowledgeBase(directory_path)
enhanced_kb.build_knowledge_base(directory_path)
model_name='./models/sentence-transformers_all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)

def rebuild():
    enhanced_kb.build_knowledge_base(directory_path)

async def streamquery(question, callback):
    context = []
    # Embed the user's question
    t1 = time.time()
    question_embedding = model.encode([question])
    t2 = time.time()
    print(f'encode:{t2-t1}')

    # Perform KNN search to find the best matches (indices and source text)
    best_matches = knn_search(question_embedding, enhanced_kb.vectorized_knowledge, k=5)
    t3 = time.time()
    print(f'knn_search:{t3-t2}')


    sourcetext=""
    for i, (index, source_text) in enumerate(best_matches, start=1):
        sourcetext += f"{i}. Index: {index}, Source Text: {source_text}"

    systemPrompt = f"Only use the following information to answer the question. Do not use anything else: {sourcetext}"
    print(f'systemPrompt:{systemPrompt}')
    print(f'systemPrompt len:{len(systemPrompt)}')

    url = get_llm_url()

    payload = {
    "model": "llama2",#"mistral-openorca",
    "prompt": question, 
    "system": systemPrompt,
    "stream": True,
    "context": context
    }

    # Convert the payload to a JSON string
    payload_json = json.dumps(payload)

    # Set the headers to specify JSON content
    headers = {
        "Content-Type": "application/json"
    }

    # Send the POST request
    r = requests.post(url, data=payload_json, headers=headers,
                      stream=True)
    r.raise_for_status()

    text = ""
    tokens = 0
    for line in r.iter_lines():
        body = json.loads(line)
        response_part = body.get('response', '')
        # the response streams one token at a time, print that as we receive it
        print(response_part, end='', flush=True)
        tokens += 1
        if response_part in ['.',':']:
            if len(text) > 0 and tokens >= 10 and text[-1] not in ['1','2','3','4','5','6','7','8','9']:
                callback(text)
                yield text.encode()
                text = ""
                tokens = 0
            else:
                text = text + response_part
        else:
            text = text + response_part

        if 'error' in body:
            raise Exception(body['error'])

        if body.get('done', False):
            pass
    