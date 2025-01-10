from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import Request 
import requests
import delegate_models

app = FastAPI()
TARGET_URL = "http://192.168.1.14:8199/v1/"

@app.api_route("/v1/{path:path}", methods=['POST'])
async def stream_request(path: str, request: Request):
    try:
        body =await request.json()
        print(body)
        body['model'] = delegate_models.MODEL
        headers = dict(request.headers)
        print(headers)
        headers.pop('content-length', None)
        # 发起POST请求
        url = TARGET_URL + path
        response = requests.post(url, json=body, headers=headers, stream=True)
        # 如果请求失败，抛出异常
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=str(e))
    
    # 定义一个生成器函数，用于流式传输响应内容
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    # 返回StreamingResponse，以流式传输响应内容
    return StreamingResponse(generate(), media_type="text/event-stream; charset=utf-8")

@app.api_route("/v1/{path:path}", methods=["GET"])
async def delegate_get(path: str, request: Request):
    if path == 'models':
        return delegate_models.models

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8020)

