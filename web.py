from datetime import datetime
import pathlib
from settings import PROMPT_PREFIX, USING_ACE, USING_WAV_CACHE, ASR_URL, AVATAR_ENABLED
from fastapi import Request, FastAPI, UploadFile, File, Form, HTTPException, Response, Query, WebSocket, Body
from fastapi.responses import HTMLResponse,StreamingResponse,FileResponse,JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tts
import json
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fileprocesspipeline import FileProcessPipeline

from settings import CHUNK_SIZE, MAX_INPUT_TOKEN, CHUNK_OVERLAP, TOP_K
from db import user_kdb_mgdb, user_prompt_info,session_mgr

chunk_size = int(os.environ.get("CHUNK_SIZE", CHUNK_SIZE))
max_input_token = int(os.environ.get("MAX_INPUT_TOKEN", MAX_INPUT_TOKEN))
chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", CHUNK_OVERLAP))
top_k = int(os.environ.get("TOP_K", TOP_K))
user_id = os.environ.get("USER_ID", "default")

UPLOAD_PATH = os.path.join(os.path.dirname(__file__), 'stores', user_id)
from routers.graphrag import set_user_path
set_user_path(UPLOAD_PATH)

from fastapi import APIRouter
router = APIRouter()

upload_directory = os.path.join(UPLOAD_PATH, "uploaded_files")
os.makedirs(upload_directory, exist_ok=True)
db_directory = os.path.join(UPLOAD_PATH, "db_files")
os.makedirs(db_directory, exist_ok=True)
res_directory = os.path.join(UPLOAD_PATH, "res_files")
os.makedirs(res_directory, exist_ok=True)
db_uri = os.path.join(UPLOAD_PATH, "milvus.db")
DEFAULT_DB_INDEX = 'default'

pipeline = FileProcessPipeline(res_directory)


from settings import USING_LLAMAINDEX, USING_LANGCHAIN, USING_RAG
from sysprompts import DEFAULT_PROMPT_TEMPLATE
from kdbmanager import kdbm

import advancerag
if USING_LLAMAINDEX:
    #mem_db = advancerag.BaseRAG(res_directory, context_window=max_input_token, chunk_size=chunk_size, chunk_overlap=chunk_overlap, top_k=top_k)
    mem_db = advancerag.AdvancedRAG(db_uri, res_directory)
    global_query_engine = mem_db.query_engine
elif USING_LANGCHAIN:
    from langchaintoolkit import MemoryVectore
    mem_db = MemoryVectore(db_directory)
    mem_db.build_knowledge_base(res_directory)
elif USING_RAG:
    from enhanceknowledgebase import EnhancedKnowledgeBase
    res_db = EnhancedKnowledgeBase(res_directory)

if AVATAR_ENABLED:
    if USING_ACE:
        from avatar.ace_a2f import audio2face,audio2face_stop
    else:
        from avatar.a2f import audio2face,audio2face_stop
else:
    def audio2face(wav):
        pass
    async def audio2face_stop():
        pass

from pydantic import BaseModel
class Item(BaseModel):
    message: str
    token: str

from db.modb_api import insert_session_data,get_context_sessionid
from agents.group import ChatBotSystem
from agents.wb_agent import initagent
ws_server = initagent()
async def formate_text(text,session_id,role=None,text_type="text",kdb_id=None):
    if session_id:
        from tts import detect_lang
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        language = detect_lang(text)
        context_data = {"session_id": session_id, "date": current_time,"kdb_id":kdb_id,
                        "context": {'text': text, "text_type": text_type, "language": language, "role": role}}
        await insert_session_data(context_data)

session_texts = {}

def get_prompt_language(language, mode):
    prompt = ""
    if language == "zh" or language == "zh-CN" or language == "zh-TW" or language == "zh-HK":
        print("使用了中文")
        if mode == "graphrag":
            from sysprompts import GRAPHRAG_PROMPT_CN
            prompt = GRAPHRAG_PROMPT_CN
        elif mode == "faq":
            from sysprompts import QUERY_PROMPT_TEMPLATE_ZH
            prompt = QUERY_PROMPT_TEMPLATE_ZH
        elif mode == "chat":
            from sysprompts import DEFAULT_ZH
            prompt = DEFAULT_ZH

    else:
        print("使用了英文")
        if mode == "graphrag":
            from sysprompts import GRAPHRAG_PROMPT_EN
            prompt = GRAPHRAG_PROMPT_EN
        elif mode == "faq":
            from sysprompts import QUERY_PROMPT_TEMPLATE_EN
            prompt = QUERY_PROMPT_TEMPLATE_EN
        elif mode == "chat":
            from sysprompts import DEFAULT_EN
            prompt = DEFAULT_EN
    print("使用的prompt：",prompt)
    return prompt

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    import json
    import asyncio
    from settings import TTS_ENABLED, USING_LLAMAINDEX,MONGODB_HOST,MONGODB_PORT,DBNAME
    from tts import detect_lang
    from wordprocess import counts_text
    from streamprocess import StreamProcess
    session_id = ''
    mode = ''
    tts_enabled = True
    message_counter = 0  # 添加计数器

    # await send_text(json.dumps({"statuses": "chat_end", "text": "chat_end"}), text_type='status')
    # await formate_text(text_to_write, session_id, role=role, text_type=text_type)
    async def send_text(text, text_type='text',role="assistant", to_end=True):
        print("to_end :",to_end)
        kdb_id = obj['kdb_id']
        print("kdb_id :",kdb_id)
        language = detect_lang(text)
        txt = json.dumps({'text': text, "text_type": text_type, "language": language})
        session_texts.setdefault(session_id, "")
        session_texts[session_id] += text

        if text_type == 'text':
            print(text)
            if TTS_ENABLED and tts_enabled:
                print(f'session_id:{session_id}')
                streaming_tts(text.strip(), session_id, mode)
                #obj = {"text":text, "session_id":session_id, "mode":mode, "locale": locale}
        elif text_type == 'code':
            print("GOT CODE")
            print(text)
        elif text_type == 'json':
            print("GOT JSON")
            print(text)
        elif text_type == 'Markdown':
            print("GOT Markdown")
            print(text)
        elif text_type == 'status':
            print("GOT status")
            print(text)
        elif text_type == 'link':
            print("GOT link")
            print(text)
        elif text_type == 'Graph':
            print("GOT Graph")
            print(text)
        try:
            await websocket.send_text(txt)
            try :
                old_kdb_id=session_mgr.get_current_kdb(session_id)
                print("old_kdb_id in web.py")
                if old_kdb_id !=kdb_id:

                    session_mgr.change_kdb(session_id,kdb_id)
            except Exception as e:
                print(e)
            if to_end:
                if session_id:
                    status_txt = json.dumps(
                        {"text":"chat_end", "text_type": "status", "language": language})
                    await  websocket.send_text(status_txt)
                    print("结束时总文本", session_texts[session_id])
                    await formate_text(session_texts[session_id], session_id, role=role, text_type=text_type,kdb_id=kdb_id)
                    session_texts[session_id] = ''
        except Exception as e:
            print("send text to websocket failed")
    proc = StreamProcess()
    async def send_stream(text, text_type = "text"):
        #print(text)
        await proc.process_chat(text, send_text_not_end)
    stop_chat = False
    query_engine = mem_db.get_query_engine()
    chat_engine = mem_db.get_chat_engine()

    async def send_text_not_end(text,text_type='text',to_end=False):
        await send_text(text, text_type=text_type,role="assistant", to_end=to_end)

    async def send_text_in_session(text):

        await send_text(text,role="assistant")
        message = await websocket.receive_text()

        obj = json.loads(message)
        await formate_text(obj['message'], session_id, role="user")
        return obj['message']

    await websocket.accept()
    while True:
        # 你可以在这里放入你的数据生成逻辑
        message = await websocket.receive_text()
        print("from ws, receive:%s"%message)#
        obj = json.loads(message)
        print("获得到的obj",obj)
        mode = obj['mode']
        message = obj['message']
        language = obj['current_language']
        await formate_text(message,session_id,role="user",text_type="text")
        if mode == 'cmd':
            session_id = message['session_id']
            ws_t[session_id] = websocket
            continue
        if 'tts_enabled' in obj.keys():
            tts_enabled = obj['tts_enabled']
        if mode == 'graphrag':
            print("=======获得到的语言:",language)

            print("mode is graphrag")
            kdb_id = obj['kdb_id']
            address = user_kdb_mgdb.get_address(kdb_id)
            ad = address["address"]
            graphrag_root_dir_path = ad + "/db_files"
            
            from msgraphrag import MSGraphRag, local_search
            
            message += get_prompt_language(language,"graphrag")
            print("gaphrag使用的prompt和问题",message)

            await local_search(query=message, root_dir=pathlib.Path(graphrag_root_dir_path), streaming=True, callback=send_stream)
            await proc.end_chat(send_text, text_type='Graph')


        elif mode == "agent" or mode == "autogen":
            from agents.function import first_call_flags
            from datetime import datetime

            async def send_text_in_agent(text,text_type):
                await send_text(text, text_type=text_type,role='assistant')

            if session_id not in ws_server.sessions:
                ws_server.sessions[session_id] = {"websocket": websocket, "message": ""}
                ws_server.chatbot_systems[session_id] = ChatBotSystem(session_id=session_id, send_cb=send_text_in_agent)

                first_call_flags[session_id] = True
            else:
                # 如果 session_id 存在，重新初始化 ChatBotSystemsend_cb
                ws_server.chatbot_systems[session_id] = ChatBotSystem(session_id=session_id,send_cb= send_text_in_agent)
                #重置首次是否发送状态标识符为True（即，可发送状态）
                first_call_flags[session_id] = True
                # 存储用户消息
            ws_server.sessions[session_id]["message"] = message
            # 调用 WebSocketServer 的聊天逻辑
            conversation_status = ws_server.conversation_status.get(session_id,True)

            if  conversation_status:
                #await ws_server.storemessage(session_id, collection,role="assistant")
                #text = ws_server.sessions[session_id].get("message", "")
                #await formate_text(text,session_id, collection,role="user",text_type="text")
                chatresult = await ws_server.initiate_conversation(send_text_in_session, session_id)

                #拿出url在这里加
                await send_text(chatresult,text_type='Markdown',role="assistant")

        elif mode =="chat":
                import sysprompts
                from llm import llm_client
                history_list=await get_context_sessionid(session_id, False)
                prompt = ""
                print("obj",obj)
                if 'prompt_name' in obj.keys() and obj['prompt_name']:
                    print("有prompt_name")
                    # prompt = getattr(sysprompts, obj["prompt_name"])
                    prompt = user_prompt_info.get_prompt_content(obj['prompt_name'])
                    print("prompt_content-----",prompt)
                if not prompt:
                    print("没有prompt_name")
                    prompt = get_prompt_language(language,"chat")
                    # prompt = getattr(sysprompts, "DEFAULT")
                    print("prompt_content-----",prompt)
                history_list.insert(0, {"role":"system", "text": prompt})
                print(history_list)
                messages = [{"role": item['role'], "content": item['text']} for item in history_list]
                #stop_chat = await advancerag.stream_chat_in_context(history_list, send_stream)
                stop_chat = await llm_client.async_chat(messages, send_stream)
                await proc.end_chat(send_text, stop_chat)
        
        elif mode =='faq':
            import settings
            import re
            kdb_id = obj['kdb_id']
            if kdb_id != '':
                history_list = await get_context_sessionid(session_id, False)
                history = []
                for index, item in enumerate(history_list):
                    his_text = item['text']
                    print("===his_text====:",his_text)
                    pattern = r'(?:\*?\s*[^a-zA-Z0-9]*\s*image_name\s*[:：]?\s*[^a-zA-Z0-9]*\s*)?(doc_\d+_page_\d+_image_([\w\u4e00-\u9fa5]+?)\.\w+)'
                    his_text_ = re.sub(pattern, '', his_text)
                    print("===his_text_clean====:", his_text_)
                    m = f"{item['role']}: {his_text_}"
                    if index < len(history_list) - 1:
                        history.append(m)
                chat_history = "\n".join(history)
                message = chat_history + "\n" + message
                prompt = get_prompt_language(language, "faq")
                my_engine = kdbm.create_or_get_rag(kdb_id=kdb_id, prompt=prompt).get_query_engine()
                print(message)
                stop_chat = await advancerag.kdb_query(my_engine, message, send_stream)
                await proc.end_chat(send_text, stop_chat)
                for node in my_engine._source_nodes:
                    print(node.node.node_id)
                    print(node.node.metadata)

        await asyncio.sleep(0.1)  # 模拟延迟

def mem_search(question):
    best_matches = mem_db.query(question)
    sourcetext=""
    #for i, (index, source_text) in enumerate(best_matches, start=1):
    #    sourcetext += f"{i}. Index: {index}, Source Text: {source_text}"
    for i, item in enumerate(best_matches):
        sourcetext += f'\n{i} source text:{item.page_content}'
    return sourcetext

def res_search(question):
    best_matches = res_db.query(question)
    sourcetext=""
    #for i, (index, source_text) in enumerate(best_matches, start=1):
    #    sourcetext += f"{i}. Index: {index}, Source Text: {source_text}"
    for i, item in enumerate(best_matches):
        print(item)
        sourcetext += f'\n{i} source text:{item[1]}'
    return sourcetext

import queue
import threading
import time
import asyncio
tts_q = queue.Queue()
ws_q = {}
ws_t = {}

STOP_TTS = False
def tts_thread():
    global STOP_TTS
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        if not tts_q.empty():
            obj = tts_q.get()
            text = obj['text']
            mode = obj['mode']
            locale = obj['locale']
            print(f"tts_thread {text}")
            haswav = False
            if USING_WAV_CACHE:
                haswav, wav = get_wave_cache(text)
            if not haswav:
                haswav,wav = tts.tts_request(text=text,mode=mode,locale=locale)
            if haswav and not STOP_TTS:
                print("has wav")
                #wav_enq(text, wav)
                session_id = obj['session_id']
                audio2face(wav)
                if session_id not in ws_q.keys():
                    continue
                #asyncio.ensure_future(send_audio_webs(session_id,wav))
                #loop.run_until_complete(send_audio_webs(session_id, wav))
                webs = ws_q[session_id]
                asyncio.run(send_audio_webs(webs, wav))
        else:
            time.sleep(0.001)
        STOP_TTS = False

async def send_audio_webs(webs, wav):
    print(f'sending audio to websocket')
    try:
        await webs.send_bytes(wav)
    except Exception as e:
        print('send websocket to audio channel failed')


t1 = threading.Thread(target=tts_thread, args=())
t1.start()
#loop = asyncio.new_event_loop()
#loop.run_until_complete(tts_thread())
def streaming_tts(text, session_id='',mode='chat', locale='mandarin'):
    obj = {"text":text, "session_id":session_id, "mode":mode, "locale": locale}
    tts_q.put(obj)

wav_q = queue.Queue()
wav_set = {}
def wav_enq(text, wav):
    #wav_q.put(wav)
    import hashlib
    # encoding GeeksforGeeks using md5 hash
    # function
    uid = hashlib.sha256(text.encode()).hexdigest()
    wav_set[text] = wav  #terry changed from uid to text
    print(uid)

def clear_tts_q():
    while not tts_q.empty():
        tts_q.get()

wav_cache = {}
def load_tts_wav():
    WAV_PATH = os.path.join(UPLOAD_PATH, "data","greetings")
    for root, dirs, files in os.walk(WAV_PATH):
        for file in files:
            fullpath = os.path.join(root, file)
            with open(fullpath, 'rb') as fp:
                wav = fp.read()
                filename = os.path.splitext(file)[0]
                wav_cache[filename] = wav

def get_wave_cache(name):
    if name in wav_cache.keys():
        return True, wav_cache[name]
    else:
        return False, None
load_tts_wav()


@router.websocket("/audio")
async def websocket_endpoint_audio(websocket: WebSocket):
    await websocket.accept()
    #await websocket.send(websocket)
    ws_q[''] = websocket
    while True:
        message = await websocket.receive_text()
        print("from audio ws, receive:%s"%message)
        obj = json.loads(message)
        session_id = obj['message']['session_id']
        ws_q[session_id] = websocket
        if not wav_q.empty():
            print("sending audio to html/js")
            wav = wav_q.get()
            await websocket.send_bytes(wav)
        await asyncio.sleep(0.01)

@router.post("/audio")
async def audio(
content: str = Form(...,title="",description=""), 
):
    counts = 0
    import tempfile
    while True:
        if counts == 10:
            print("timeout return error!")
            return JSONResponse(
            status_code=404,
            content={"message": "Not found"}
            )
        if content in wav_set.keys():
            wav = wav_set[content]
            fpath = tempfile.mktemp(".wav")
            with open(fpath, 'wb') as fp:
                fp.write(wav)
            wav_set.pop(content)
            return FileResponse(fpath, media_type="audio/x-wav")
        else:
            time.sleep(0.5)
            counts += 1

@router.post("/crawl")
async def crawl(
url: str = Form(...,title="",description=""), 
):
    from utils import getArticleText, getUrls
    urls = getUrls(url)

    for url in urls:
        text = getArticleText(url)
        filename = url.replace(":","").replace("/","")
        file_path = os.path.join(upload_directory, f'{filename}.txt')
        with open(file_path, "w", encoding='utf-8') as buffer:
            buffer.write(text)

@router.post("/asr/generate")
async def generate(file: UploadFile = File(...)):
    import asr
    import tempfile
    filename = os.path.join(tempfile.gettempdir(), f'{time.time()}{file.filename}')
    print(file.filename)
    print(file.content_type)
    audio = file.file.read()
    print(len(audio))
    with open(file=filename, mode='wb') as fp:
        fp.write(audio)

    return asr.upload_file([filename], ASR_URL)
            
@router.post("/stop_audio")
async def stop_audio(
):
    global STOP_TTS
    advancerag.stop_streaming()
    STOP_TTS = True
    clear_tts_q()
    await audio2face_stop()
    return {}

def replace_messages_with_rag(body):
    from llama_index.core.schema import MetadataMode
    messages = body['messages']
    question = messages[-1]['content']
    new_quesion="Condensed question: " + question + "\nContext:"
    content = mem_db.retrieve(question)
    for c in content:
        new_quesion += c.get_content(metadata_mode=MetadataMode.LLM) + "\n"
    messages[-1]['content'] = new_quesion

from settings import get_llm_base_url
TARGET_URL = get_llm_base_url()
if not TARGET_URL.endswith("/"):
    TARGET_URL += "/"
import requests
import delegate_models

@router.api_route("/v1/{path:path}", methods=['POST'])
async def stream_request(path: str, request: Request):
    try:
        body =await request.json()
        print(body)
        body['model'] = delegate_models.MODEL
        replace_messages_with_rag(body)
        print(body)
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

@router.api_route("/v1/{path:path}", methods=["GET"])
async def delegate_get(path: str, request: Request):
    if path == 'models':
        return delegate_models.models

@router.post("/audiochat")
async def audiochat(
        session_id: str = Form(...,title="",description=""),
        mode: str = Form(...,title="",description=""),
        locale:  Optional[str] = Form(...,title="",description=""),
        file: UploadFile = File(...)):
    print(f"receive audio:{session_id}, mode:{mode}, locale:{locale}")
    import asr
    import tempfile
    filename = os.path.join(tempfile.gettempdir(), f'{time.time()}{file.filename}')
    print(file.filename)
    print(file.content_type)
    audio = file.file.read()
    print(len(audio))
    with open(file=filename, mode='wb') as fp:
        fp.write(audio)

    obj = asr.upload_file([filename], ASR_URL)
    message = obj['text']
    if session_id in ws_t.keys():
        txt = json.dumps({'text': message, "text_type": "text", "language": "zh_cn", "role":"user"})
        await ws_t[session_id].send_text(txt)

    async def send_audio(text, text_type='text'):
        print(text)
        if text_type == 'text':
            streaming_tts(text.strip(), session_id, mode, locale)
        if session_id in ws_t.keys():
            txt = json.dumps({'text': text, "text_type": text_type, "language": "zh_cn", "role":"assistant"})
            await ws_t[session_id].send_text(txt)

    async def send_stream(text):
        await proc.process_chat(text, send_audio)

    from streamprocess import StreamProcess
    proc = StreamProcess()
    if mode =="faq":
        query_engine = mem_db.get_query_engine()
        #message = PROMPT_PREFIX + message
        message = DEFAULT_PROMPT_TEMPLATE.format(text=message)
        #stop_chat = await llamaindex.kdb_chat(query_engine, message, send_stream)
        stop_chat = await advancerag.kdb_query(query_engine, message, send_stream)
        await proc.end_chat(send_audio, stop_chat)
    else:
        stop_chat = await advancerag.stream_chat(message, send_stream)
        await proc.end_chat(send_audio, stop_chat)
    return obj

@router.route('/streamtest')
def stream_audio(request: Request):
    def generate():
        while True:
          time.sleep(1)
          with open("data/streamtest.mp3", "rb") as audio_file:
            data = audio_file.read(1024)
            while data:
                yield data
                data = audio_file.read(1024)

    return StreamingResponse(generate(), media_type="audio/mpeg")

@router.post("/generate")
async def generate(
    question: str = Body(..., embed=True),
):
    print(question)
    result = await advancerag.achat(question)
    return {"answer":result, "question":question}

@router.post("/docgen")
async def upload_files(template_file: UploadFile = File(...), context_file: UploadFile = File(...)):
    file_path = os.path.join(upload_directory, template_file.filename)
    out_file_path = os.path.join(upload_directory, "out_"+template_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(template_file.file, buffer)
    cfile_path = os.path.join(upload_directory, context_file.filename)
    with open(cfile_path, "wb") as buffer:
        shutil.copyfileobj(context_file.file, buffer)
    #content = template_file.file.read()
    #context = context_file.file.read()
    from docfill import docx_to_txt
    out = docx_to_txt(file_path, out_file_path, cfile_path)
    return {"result":True, "filepath": "out_"+template_file.filename}

@router.get("/download")
async def download_file(filepath: str): 
    out_file_path = os.path.join(upload_directory,filepath)
    return FileResponse(out_file_path, filename=filepath)#media_type="application/word")

"""
cert_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "certs", "certificate.crt")
key_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "certs", "private.key")

if os.path.isfile(cert_file) and os.path.isfile(key_file):
    app.certfile = cert_file
    app.keyfile = key_file
"""
if __name__ == "__main__":
    import uvicorn
    app = FastAPI()
    #from routers import graphrag
    #app.include_router(graphrag.router, prefix="/graphrag", tags=["graphrag"])
    # 挂载 static 目录
    app.mount("/static", StaticFiles(directory="static"), name="static")
    #app.mount("/", StaticFiles(directory="static", html=True), name="static")
    # 设置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源，或者你可以指定来源 ["http://localhost:3000"]
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
