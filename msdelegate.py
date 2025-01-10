from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import Request 
import requests
import delegate_models
from msgraphrag import MSGraphRag
import os

STREAMING_ENABLED = False
app = FastAPI()
TARGET_URL = "http://192.168.1.14:8199/v1/"

BASE_DIR = "/media/terry/798e0dfc-0000-441f-8bbe-d96a237a89aa/prjs/zk"
INPUT_DIR = os.path.join(BASE_DIR, "output/20240731-165731/artifacts")
LANCEDB_URI = f"{BASE_DIR}/lancedb"

msg = MSGraphRag()
msg.init_stores(INPUT_DIR, LANCEDB_URI)
#print(msg.search(query).response)

def get_chat_obj(message):
    obj = delegate_models.chat_completion
    obj['choices'][0]['message']['content'] = message
    return obj

@app.api_route("/v1/{path:path}", methods=['POST'])
async def stream_request(path: str, request: Request):
    from graphrag.query.llm.base import BaseLLMCallback
    cb = BaseLLMCallback()
    try:
        body =await request.json()
        print(body)
        body['model'] = delegate_models.MODEL
        messages = body['messages']
        question = messages[-1]['content']
        if not body['stream'] or not STREAMING_ENABLED:
            resp = msg.search(question)
            ret = get_chat_obj(resp.response)
            print(ret)
            return ret
        headers = dict(request.headers)
        print(headers)
        headers.pop('content-length', None)
        # 发起POST请求
        result = await msg.asearch(question,cb)
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=str(e))
    
    # 定义一个生成器函数，用于流式传输响应内容
    def generate():
        for chunk in cb.response:
            if chunk:
                yield chunk

    # 返回StreamingResponse，以流式传输响应内容
    return StreamingResponse(generate(), media_type="text/event-stream; charset=utf-8")

@app.api_route("/v1/{path:path}", methods=["GET"])
async def delegate_get(path: str, request: Request):
    if path == 'models':
        return delegate_models.graphrag_models

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8022)

