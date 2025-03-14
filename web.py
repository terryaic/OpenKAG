from datetime import datetime
import pathlib


import queue
from settings import PROMPT_PREFIX, USING_ACE, USING_WAV_CACHE, ASR_URL, AVATAR_ENABLED
from fastapi import Request, FastAPI, UploadFile, File, Form, HTTPException, Response, Query, WebSocket, Body
from fastapi.responses import HTMLResponse,StreamingResponse,FileResponse,JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
import os
import shutil
import tts
import json
from typing import Optional
from fastapi.staticfiles import StaticFiles
from auth.check_login import check_login
from apis.version1.route_login import get_resource
from fileprocesspipeline import FileProcessPipeline
from settings import CHUNK_SIZE, MAX_INPUT_TOKEN, CHUNK_OVERLAP, TOP_K
from db import user_kdb_mgdb, user_prompt_info,session_mgr,session_file_db
import tempfile

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


from settings import USING_LLAMAINDEX, USING_LANGCHAIN, USING_RAG,TIMEOUT_RELEASE_INDEX
import sysprompts
from sysprompts import DEFAULT_PROMPT_TEMPLATE
from kdbmanager import kdbm,start_kdbm_monitor

start_kdbm_monitor(TIMEOUT_RELEASE_INDEX)

import advancerag
mem_db: advancerag.AdvancedRAG = None
async def init_mem_db():
    global mem_db
    if not mem_db:
        mem_db = advancerag.AdvancedRAG()
        storage_dir = os.path.join(UPLOAD_PATH, "storage")
        await mem_db.init(db_uri, res_directory, storage_dir)


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
        # from markdown_it.rules_block import reference
        # if reference:
        #     file_data={"session_id": session_id, "date": current_time,"kdb_id":kdb_id,
        #                 "context": {'text': reference, "text_type": "file", "language": language, "role": "user"}}
        #     await insert_session_data(file_data)
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

def get_system_prompt(language, mode):
    prompt = ""
    if language == "zh" or language == "zh-CN" or language == "zh-TW" or language == "zh-HK":
        print("使用了中文")
        if mode == "graphrag":
            from sysprompts import GRAPHRAG_PROMPT_CN
            prompt = GRAPHRAG_PROMPT_CN
        elif mode == "faq":
            from sysprompts import SYSTEM_PROMPT_TEMPLATE_ZH
            prompt = SYSTEM_PROMPT_TEMPLATE_ZH
        elif mode == "chat":

            from sysprompts import DEFAULT_ZH
            prompt = DEFAULT_ZH

    else:
        print("使用了英文")
        if mode == "graphrag":
            from sysprompts import GRAPHRAG_PROMPT_EN
            prompt = GRAPHRAG_PROMPT_EN
        elif mode == "faq":
            from sysprompts import SYSTEM_PROMPT_TEMPLATE_EN
            prompt = SYSTEM_PROMPT_TEMPLATE_EN
        elif mode == "chat":
            from sysprompts import DEFAULT_EN
            prompt = DEFAULT_EN
    print("使用的prompt：",prompt)
    return prompt

def get_system_chat_prompt(language, mode):
    prompt = ""
    if language == "zh" or language == "zh-CN" or language == "zh-TW" or language == "zh-HK":
        print("使用了中文")
        if mode == "graphrag":
            from sysprompts import GRAPHRAG_PROMPT_CN
            prompt = GRAPHRAG_PROMPT_CN
        elif mode == "faq":
            from sysprompts import SYSTEM_CHAT_PROMPT_TEMPLATE_ZH
            prompt = SYSTEM_CHAT_PROMPT_TEMPLATE_ZH
        elif mode == "chat":
            from sysprompts import DEFAULT_CHAT_ZH
            prompt = DEFAULT_CHAT_ZH
    else:
        print("使用了英文")
        if mode == "graphrag":
            from sysprompts import GRAPHRAG_PROMPT_EN
            prompt = GRAPHRAG_PROMPT_EN
        elif mode == "faq":
            from sysprompts import SYSTEM_PROMPT_TEMPLATE_EN
            prompt = SYSTEM_PROMPT_TEMPLATE_EN
        elif mode == "chat":
            from sysprompts import DEFAULT_EN
            prompt = DEFAULT_EN
    print("使用的prompt：",prompt)
    return prompt

async def get_chat_history(session_id):
    import re
    history_list = await get_context_sessionid(session_id, False)
    history = []
    for index, item in enumerate(history_list):
        if item["text_type"] == "rag_node":
            continue
        his_text = item['text']
        if isinstance(his_text, list):
            print(f"Skipping item at index {index} because it is a list.")
            continue
        print("===his_text====:",his_text)
        pattern = r'(?:\*?\s*[^a-zA-Z0-9]*\s*image_name\s*[:：]?\s*[^a-zA-Z0-9]*\s*)?(doc_\d+_page_\d+_image_([\w\u4e00-\u9fa5]+?)\.\w+)'
        his_text_ = re.sub(pattern, '', his_text)
        print("===his_text_clean====:", his_text_)
        #m = f"{item['role']}: {his_text_}"  TERRY
        m = (item['role'], item['text'])
        if index < len(history_list) - 1:
            history.append(m)
    return history

async def get_query_engine(language, kdb_id, session_id):
    history = await get_chat_history(session_id)
    #chat_history = "\n".join(history)       TERRY
    #message = chat_history + "\n" + message TERRY
    prompt = get_prompt_language(language, "faq")
    system_prompt = get_system_prompt(language, "faq")
    adrag = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    my_engine = adrag.get_query_engine(system_prompt, prompt, history)
    return my_engine

async def get_chat_engine(language, kdb_id, session_id):
    history = await get_chat_history(session_id)
    #chat_history = "\n".join(history)       TERRY
    #message = chat_history + "\n" + message TERRY
    prompt = get_prompt_language(language, "faq")
    system_prompt = get_system_chat_prompt(language, "faq")
    adrag = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    my_engine = adrag.get_query_engine(system_prompt, prompt, history)
    return my_engine

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    import json
    import asyncio
    from settings import TTS_ENABLED, USING_LLAMAINDEX,MONGODB_HOST,MONGODB_PORT,DBNAME
    from tts import detect_lang
    from wordprocess import counts_text
    from streamprocess import StreamProcess
    from advancerag import ChatSession
    session_id = ''
    mode = ''
    tts_enabled = True
    message_counter = 0  # 添加计数器

    # await send_text(json.dumps({"statuses": "chat_end", "text": "chat_end"}), text_type='status')
    # await formate_text(text_to_write, session_id, role=role, text_type=text_type)
    async def send_text(text, text_type='text',role="assistant", to_end=True, store_history=True):
        print("to_end :",to_end)
        kdb_id = obj['kdb_id']
        print("kdb_id :",kdb_id)
        language = detect_lang(text)
        txt = json.dumps({'text': text, "text_type": text_type, "language": language})
        session_texts.setdefault(session_id, "")
        if text_type == "rag_node" or text_type == "stat":
            session_texts[session_id] = text
        else:
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
                if store_history:
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

    async def send_text_not_end(text,text_type='text',to_end=False):
        await send_text(text, text_type=text_type,role="assistant", to_end=to_end)

    async def send_text_in_session(text):

        await send_text(text,role="assistant")
        message = await websocket.receive_text()

        obj = json.loads(message)
        print("message是",obj['message'])
        await formate_text(obj['message'], session_id, role="user")
        return obj['message']

    await websocket.accept()
    while True:
        from auth.check_login import check_login
        login_status = await check_login(websocket)
        print("login_status",login_status)
        if login_status and login_status.get("action") == "redirect":
            txt={"text": "reload", "text_type": "redirect"}
            await websocket.send_json(txt)
            print("发送成功",txt)# 发送重定向指令
            await websocket.close()  # 关闭 WebSocket
            return
        # 你可以在这里放入你的数据生成逻辑
        message = await websocket.receive_text()
        print("from ws, receive:%s"%message)#
        obj = json.loads(message)
        print("获得到的obj",obj)
        reference = obj.get("reference", None)
        if reference:
            print("reference-------", reference)
            await formate_text(reference, session_id, role="user", text_type="file")
            continue
        mode = obj['mode']
        message = obj['message']
        language = obj['current_language']
        print("记录信息History", message)
        await formate_text(message,session_id,role="user",text_type="text")
        if mode == 'cmd':
            session_id = message['session_id']
            ws_t[session_id] = websocket
            ws_s[session_id] = ChatSession()
            continue
        proc._reset()
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
                if True:
                    reference_list = session_file_db.get_reference_list(session_id)
                    print("reference_list in web,oy",reference_list)
                    print("Type of reference_list:", type(reference_list))
                    if reference_list and len(reference_list) > 0:
                        print("reference_list 非空，进入处理逻辑")
                        for ref in reference_list:
                            print("当前处理的 ref:", ref)
                            respath = ref.get("respath")  # 获取路径
                            print("当前处理的 respath:", respath)
                            if respath:
                                try:
                                    with open(respath, 'r', encoding='utf-8') as file:
                                        file_content = file.read()
                                        prompt += f"\n{file_content}"
                                        print("文件内容已拼接:", file_content)
                                except FileNotFoundError:
                                    print(f"文件未找到: {respath}")
                                except IOError as e:
                                    print(f"读取文件时发生错误: {e}")
                    else:
                        print("reference_list 为空或格式错误，未拼接任何内容aaaaaaaaaa")
                print("=============================")
                print("新的prompt是：",prompt)
                print("=============================")
                history_list.insert(0, {"role":"system", "text": prompt})
                print(history_list)
                #file的信息是列表，排除，deepseek会报错，没有做转str处理
                messages = [
                    {"role": item['role'], "content": item['text']}
                    for item in history_list if not isinstance(item['text'], list)
                ]
                #stop_chat = await advancerag.stream_chat_in_context(history_list, send_stream)
                stop_chat = await llm_client.async_chat(messages, send_stream, ws_s[session_id])
                await proc.end_chat(send_text, stop_chat)
        
        elif mode =='faq':
            kdb_id = obj['kdb_id']
            if kdb_id != '':
                my_engine = await get_query_engine(language=language, kdb_id=kdb_id, session_id=session_id)
                print(message)
                stop_chat = await advancerag.kdb_query(my_engine, message, send_stream, ws_s[session_id])
                nodes = {}
                # print("rag_node的信息是======>",my_engine._source_nodes)
                for node_with_score in my_engine._source_nodes:
                    metadata = node_with_score.metadata
                    node_id = node_with_score.node.id_  # 获取 metadata
                    nodes[node_id] = {"name":metadata.get("file_name"),"size":metadata.get("file_size"),"type":metadata.get("file_type"),"id":node_id,"score": node_with_score.score}
                # 对 nodes 按 score 排序，由大到小
                nodes = sorted(nodes.values(), key=lambda x: x["score"], reverse=True)
                text = await proc.end_chat(send_text, stop_chat)
                # 发送node信息
                if obj['rag_node']:
                    await send_text(nodes, "rag_node")
        stat = {"completion_tokens": proc.total_tokens, "first_token_latency": proc.first_token_time - proc.request_time, "last_token_latency": proc.last_token_time - proc.request_time, "throughput": proc.total_tokens * 1.0 / (proc.last_token_time - proc.request_time)}
        await send_text(stat, "stat", store_history=False)

        await asyncio.sleep(0.1)  # 模拟延迟

@router.post("/stop_gen/{session_id}")
async def stop_gen(
    session_id: str
):
    advancerag.stop_streaming(ws_s[session_id])
    return {"ret": True}

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

import threading
import time
import asyncio
tts_q = queue.Queue()
ws_q = {}
ws_t = {}
ws_s = {}

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

def stop_audio_fn(session_id):
    if session_id in stream_tts_q.keys():
        tts = stream_tts_q[session_id]
        while not tts.empty():
            tts.get()
    if AVATAR_ENABLED:
        a2f_srv = avatar_srv[session_id].service
        a2f_srv.clear_queues()

@router.post("/stop_audio/{session_id}")
async def stop_audio_session(session_id: str
):
    #session = ws_s[session_id]
    #advancerag.stop_streaming(session)
    stop_audio_fn(session_id)
    return {"ret": True}

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
    ws_s[session_id] = advancerag.ChatSession()
    await init_mem_db()
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
        stop_chat = await advancerag.kdb_query(query_engine, message, send_stream, ws_s[session_id])
        await proc.end_chat(send_audio, stop_chat)
    else:
        stop_chat = await advancerag.stream_chat(message, send_stream, ws_s[session_id])
        await proc.end_chat(send_audio, stop_chat)
    return obj

stream_tts_q = {}

if AVATAR_ENABLED:
    from avatar.avatar_driving import AvatarDrivingService
    avatar_drv = AvatarDrivingService("avatar/avatar.json")
    avatar_srv = {}
    def avatar_check():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            for key in avatar_srv.keys():
                handle = avatar_srv[key]
                a2f_srv = handle.service
                if not handle._released and a2f_srv.active_time + handle.timeout < time.time():
                    print("time out release avatar:", a2f_srv.ws_url)
                    handle.release()
                    asyncio.run(avatar_drv.stop_driving(a2f_srv.ws_url))
            time.sleep(1)

avatar_thread = None
@router.get("/avatarchat/{user}", include_in_schema=False)
async def avatarchat_user(user: str, request: Request):
    print("got user:", user)
    global avatar_thread
    import uuid
    session_id = uuid.uuid4().hex
    from avatar.a2f_v2 import pool
    from avatar.main import db_client
    from settings import avatar_configs, AVATAR_TIMEOUT
    if avatar_thread is None:
        avatar_thread = threading.Thread(target=avatar_check)
        avatar_thread.start()
    if user == 'undefined':
        return {"ret":False}
    handle = pool.request_service()
    if handle:
        handle.timeout = AVATAR_TIMEOUT
        a2f_srv = handle.service
        ws_url = None
        avatar_id = ""
        speaker_id = ""
        template_name = "avatarchat_test.html"
        if user == 'autism':
            template_name = "avatarchat_autism.html"
            ws_url = avatar_configs["autism"]["ws_url"]
            avatar_id = avatar_configs["autism"]['avatar_id']
            handle.timeout = AVATAR_TIMEOUT * 5
        if ws_url is None:
            ws_url = avatar_configs["test"]["ws_url"]
            avatar_id = avatar_configs["test"]['avatar_id']
        avatar_srv[session_id] = handle
        user_info = await db_client.get_user_info(user)
        if user_info:
            avatar_id = user_info['avatar_id']
        avatar = await db_client.get_avatar(avatar_id)
        if avatar is None:
            avatar = await db_client.get_avatar_by_name(user)
        if avatar:
            speaker_id = avatar["_id"]
            avatar_id = avatar["_id"]
            ws_url = await avatar_drv.start_driving(a2f_srv.ws_url,avatar_id)
        print(f"create_session:{user} with {avatar_id}")
        if session_id not in ws_s.keys():
            ws_s[session_id] = advancerag.ChatSession(user)
        session_mgr.create_session(user, session_id, "private chat with avatar", "",extra_info=avatar_id)
        time.sleep(5)
        return templates.TemplateResponse(template_name,  {"request": request, "mode": "chat", 
                                "session_id": session_id, "ws_url": ws_url, "avatar_id": avatar_id,
                                "prompt_name": user, "speaker_id":speaker_id, "timeout": handle.timeout
                                                })
    else:
        return templates.TemplateResponse("error.html", {"request": request})

@router.post("/audiostreamchat")
async def audiostreamchat(
        session_id: str = Form(...,title="",description=""),
        mode: str = Form(...,title="",description=""),
        locale:  Optional[str] = Form(...,title="",description=""),
        file: UploadFile = File(...),
        kdb_id:  Optional[str] = Form(default="",title="",description=""),
        prompt_name: Optional[str] = Form(default="",title="",description=""),
        speaker_id: Optional[str] = Form(default="",title="",description="")):
    print(f"receive audio:{session_id}, mode:{mode}, locale:{locale}")
    if session_id not in ws_s.keys():
        ws_s[session_id] = advancerag.ChatSession()
    else:
        ws_s[session_id].stop_chat = False
    if session_id not in stream_tts_q.keys():
        stream_tts_q[session_id] = queue.Queue()
    await init_mem_db()
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
    if obj:
        message = obj['text']
        text = await audiostreamchat_impl(message, session_id, mode, locale, kdb_id, prompt_name, speaker_id, user=ws_s[session_id].user, load_long_mem=True)
    else:
        text = ""
    return {"text": text, "text_type": "text", "language": "zh_cn", "role":"assistant"}

@router.post("/audiostreamchat_inj")
async def audiostreamchat_inj(
        session_id: str = Form(...,title="",description=""),
        mode: str = Form(...,title="",description=""),
        message: Optional[str] = Form(default="",title="",description=""),
        locale:  Optional[str] = Form(default="",title="",description=""),
        kdb_id:  Optional[str] = Form(default="",title="",description=""),
        prompt_name: Optional[str] = Form(default="",title="",description=""),
        speaker_id: Optional[str] = Form(default="",title="",description="")):
    if session_id not in ws_s.keys():
        ws_s[session_id] = advancerag.ChatSession()
    else:
        ws_s[session_id].stop_chat = False
    if session_id not in stream_tts_q.keys():
        stream_tts_q[session_id] = queue.Queue()
    text = await audiostreamchat_impl(message, session_id, mode, locale, kdb_id, prompt_name, speaker_id, user=ws_s[session_id].user, load_long_mem=True)
    return {"text": text, "text_type": "text", "language": "zh_cn", "role":"assistant"}

def refine_text(text):
    import re
    # 同时匹配中文括号（ ）和英文括号( )
    pattern = r'（(.*?)）|\((.*?)\)'
    
    # 查找所有符合条件的括号内容
    matches = re.findall(pattern, text)
    
    # 将括号内的内容整合到一个列表中
    instruct_list = []
    for match in matches:
        # match返回的是一个tuple，如：("眼睛闪闪发亮", "") 或 ("", "温柔地笑着")
        # 第一个元素不为空字符串时，表示匹配到了中文括号，第二个元素不为空时表示匹配到了英文括号
        if match[0]:
            instruct_list.append(match[0])
        else:
            instruct_list.append(match[1])
    
    # 通过正则替换，将所有括号及其内容从原文本中移除
    text_cleaned = re.sub(pattern, '', text)
    
    # 返回结果，括号内容列表放在 "instruct" 中，去除括号后剩余的文本放在 "text" 中
    result = {
        "instruct": instruct_list,
        "text": text_cleaned.strip()
    }
    
    return result

async def audiostreamchat_impl(message, session_id, mode, locale, kdb_id, prompt_name, speaker_id, user=None, load_long_mem=False):
    from llm import llm_client
    if session_id in ws_t.keys():
        txt = json.dumps({'text': message, "text_type": "text", "language": "zh_cn", "role":"user"})
        await ws_t[session_id].send_text(txt)

    async def send_audio(text, text_type='text'):
        if text_type == 'text':
            print(f"put q:{text}")
            #obj = {"text":text, "speaker_id": speaker_id}
            obj = refine_text(text)
            if obj['text']:
                obj['speaker_id'] = speaker_id
                stream_tts_q[session_id].put(obj)
        if session_id in ws_t.keys():
            txt = json.dumps({'text': text, "text_type": text_type, "language": "zh_cn", "role":"assistant"})
            await ws_t[session_id].send_text(txt)

    async def send_stream(text):
        await proc.process_chat(text, send_audio)

    if prompt_name:
        import avatar_prompts
        prompt = getattr(avatar_prompts, prompt_name)
        #prompt = user_prompt_info.get_prompt_content(prompt_name])
    else:
        prompt = sysprompts.BUDDY_CHAT_ZH

    if AVATAR_ENABLED:
        from avatar.main import db_client
        if speaker_id:
            avatar = await db_client.get_avatar(avatar_id=speaker_id)
            if 'character' in avatar['assets'].keys():
                prompt += "\n以下是你的个人设定：" + avatar['assets']['character'] + "\n"
        if user:
            user_info = await db_client.get_user_info(user)
            key_value_str = ', '.join(f"{k}:{v}" for k, v in user_info['user_profile'].items())
            prompt += "\n以下是对话对象的个人资料：" + key_value_str + "\n"
    
    if load_long_mem:
        sessions = session_mgr.list_session_with_extra(user, speaker_id)
        history_list = []
        for session in sessions:
            print(session)
            history = await get_context_sessionid(session['session_id'], False)
            history_list.extend(history)
    else:
        history_list =await get_context_sessionid(session_id, False)
    history_list.insert(0, {"role":"system", "text": prompt})
    history_list.append({"role":"user", "text": message})
    await formate_text(message, session_id, "user")
    messages = [
        {"role": item['role'], "content": item['text']}
        for item in history_list if not isinstance(item['text'], list)
    ]

    print(messages)
    from streamprocess import StreamProcess
    proc = StreamProcess()
    if mode =="faq" and kdb_id != '':
        query_engine = await get_chat_engine(language="zh-CN", kdb_id=kdb_id, session_id=session_id)
        stop_chat = await advancerag.kdb_query(query_engine, message, send_stream, ws_s[session_id])
    else:
        #stop_chat = await advancerag.stream_chat(message, send_stream, ws_s[session_id])
        #stop_chat = await advancerag.stream_chat_in_context(messages, send_stream, ws_s[session_id])
        stop_chat = await llm_client.async_chat(messages, send_stream, ws_s[session_id])
    all_text = await proc.end_chat(send_audio, stop_chat)
    await formate_text(all_text, session_id, "assistant")
    ws_s[session_id].stop_chat = True
    return all_text

@router.post("/streaming_chat/{session_id}")
async def streaming_chat(session_id: str):
    import httpx
    from settings import STREAM_TTS_URL
    if session_id not in ws_s.keys():
        ws_s[session_id] = advancerag.ChatSession()
    if session_id not in stream_tts_q.keys():
        stream_tts_q[session_id] = queue.Queue()
    session = ws_s[session_id]
    my_q = stream_tts_q[session_id]
    speaker_id = ""
    async def generator():
        if AVATAR_ENABLED:
            a2f_srv = avatar_srv[session_id].service
        while not session.stop_chat or not my_q.empty():
            if my_q.empty():
                yield b'\x00\x00'
                time.sleep(0.01)
                continue
            msg = my_q.get()
            print(msg)
            text = msg['text']
            speaker_id = msg['speaker_id']
            if text is None or text.strip() == "":
                continue
            try:
              async with httpx.AsyncClient() as client:
                # open a streaming POST request
                async with client.stream(
                    "POST",
                    STREAM_TTS_URL,
                    data={"tts_text": text, "speaker_id": speaker_id},
                ) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_bytes():
                        if AVATAR_ENABLED:
                            #chunk2face(chunk)
                            a2f_srv.chunk2face(chunk)
                        yield chunk
            except Exception as e:
              print(e)
              break
        stream_tts_q.pop(session_id)
        #ws_s.pop(session_id)
        ws_s[session_id].stop_chat = False
    return StreamingResponse(generator())

#from fastapi import BackgroundTasks
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)
text_q = queue.Queue()
stop_chat = False

async def long_running_task(mem_db, mode, message):
    global stop_chat
    stop_chat = False
    # Offload blocking task to a thread pool
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, blocking_llm_query, mem_db, mode, message)
    stop_chat = True

@router.post("/avatarchat")
async def avatarchat(
        file: UploadFile = File(...),
        session_id: str = Form(...,title="",description=""),
        mode: str = Form(...,title="",description=""),
        locale:  Optional[str] = Form(default="",title="",description=""),
        kdb_id:  Optional[str] = Form(default="",title="",description="")):
    print(f"receive audio:{session_id}, mode:{mode}, locale:{locale}")
    await init_mem_db()
    import asr
    import tempfile
    import httpx
    from settings import STREAM_TTS_URL

    filename = os.path.join(tempfile.gettempdir(), f'{time.time()}{file.filename}')
    print(file.filename)
    print(file.content_type)
    audio = file.file.read()
    print(len(audio))
    with open(file=filename, mode='wb') as fp:
        fp.write(audio)

    obj = asr.upload_file([filename], ASR_URL)
    message = obj['text']
    if kdb_id is not None and kdb_id != "":
        adrag = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    else:
        adrag = mem_db
    asyncio.create_task(long_running_task(adrag, mode, message))

    async def generator():
        global text_q,stop_chat
        if AVATAR_ENABLED:
            from avatar.a2f import chunk2face
        while not stop_chat or not text_q.empty():
            text = text_q.get()
            print(text)
            try:
              async with httpx.AsyncClient() as client:
                # open a streaming POST request
                async with client.stream(
                    "POST",
                    STREAM_TTS_URL,
                    data={"tts_text": text},
                ) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_bytes():
                        if AVATAR_ENABLED:
                            chunk2face(chunk)
                        yield chunk
            except Exception as e:
              text_q.clear()
              break

    return StreamingResponse(generator())

def blocking_llm_query(mem_db, mode, message):
    print("blocking query")
    from streamprocess import StreamProcessSync
    from llm import llm_client
    proc = StreamProcessSync()

    def send_stream(text, text_type = "text"):
        proc.process_chat(text, send_audio)

    def send_audio(text, text_type='text'):
        global text_q
        text_q.put(text)

    def llm_call(mem_db, mode, message):
        print("call",mode,message)
        if mode =="faq":
            language = "zh-CN"
            prompt = get_prompt_language(language, "faq")
            system_prompt = get_system_prompt(language, "faq")
            mem_db.get_query_engine(system_prompt, prompt)
            text = mem_db.query(message)
            send_audio(text=text)
        else:
            text = llm_client.chat_with_openai(message, callback=send_stream)
            proc.end_chat(send_audio)

    #asyncio.create_task(llm_call(mem_db, mode, message, stop_chat))
    llm_call(mem_db, mode, message)

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

@router.post("/kdbgenerate/{kdb_id}")
async def kdbgenerate(
    kdb_id: str,
    question: str = Body(..., embed=True),
):
    print("获得到的kdb是：",kdb_id)
    print("获得到的问题是：",question)
    adrag = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    prompt = get_prompt_language("zh-CN", "faq")
    system_prompt = get_system_prompt("zh-CN", "faq")
    my_engine = adrag.get_query_engine(system_prompt, prompt)
    from streamprocess import StreamProcess
    proc = StreamProcess()
    
    full_response, stop_chat = await advancerag.kdb_query_nc(my_engine, question)
    print("回答是",full_response)
    print("回答是",stop_chat)

    return {"answer":full_response, "question":question}

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


@router.get("/export_history", include_in_schema=False)
async def show_kdb(request: Request):
    response = await check_login(request)
    if response:
        return response
    return templates.TemplateResponse("export_history.html", {"request": request, "resources": get_resource(request, "export_history")})

def get_readable_time(timestamp):
    # 转换为 datetime 对象
    dt_object = datetime.fromtimestamp(timestamp)
    # 输出为可读格式
    readable_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    return readable_time
    
@router.post("/get_session_info")
async def get_session_info(request: Request):
    from db.session_mgr import list_session
    user_id = request.cookies.get("current_user")

    conversations = list_session(user_id)

    # 处理获取的信息
    
    for session_info in conversations:
        # 创建时间
        session_info['create_time'] = get_readable_time(session_info['create_time'])
        
        # 删除不需要的字段（判断字段是否存在）
        session_info.pop('reference', None)
        session_info.pop('kdb_id', None)
        session_info.pop('update_time', None)

    print("当前的聊天记录是",conversations)
    return conversations


@router.post("/export_session_context")
async def export_session_context(request: Request):
    from db.session_mgr import get_session
    
    body = await request.json()  # 获取请求体

    # 获取 session_list 参数
    session_list = body.get('session_list')
    if not session_list:
        return 
    
    historys_list = []
    session_info_list = []

    if isinstance(session_list,list):
        for session_id in session_list:
            history = await get_context_sessionid(session_id)
            session_info = get_session(session_id)
            historys_list.append(history)
            session_info_list.append(session_info)
    else:
        print("不是list")

    historys_json = []

    for session, history in zip(session_info_list, historys_list):
        chat_info = {}
        chat_info["title"] = session.get("title")
        chat_info["create_time"] = get_readable_time(session.get("create_time"))
        
        session_chat = []
        single_chat = {}
        for chat in reversed(history):
            if (chat.get("text_type") == "text" or chat.get("text_type") == "Graph") and chat.get("role") == "user":
                single_chat["question"] = chat.get("text")
            elif (chat.get("text_type") == "text" or chat.get("text_type") == "Graph") and chat.get("role") == "assistant":
                single_chat["answer"] = chat.get("text")
                session_chat.append(single_chat)
                single_chat = {}      

        chat_info["chat_history"] = session_chat

        historys_json.append(chat_info)   
    
    print("导出的记录是",historys_json)

    # 生成临时 JSON 文件（代码同之前示例）
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "chat_history.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(historys_json, f, ensure_ascii=False, indent=4)
    
    return FileResponse(file_path, media_type="application/json", filename="chat_history.json")


@router.post("/reset_session_name")
async def reset_session_name(request: Request):
    body = await request.json()  # 获取请求体

    # 获取 session_id 参数
    session_id = body.get('session_id')
    new_title = body.get('new_title')

    result = session_mgr.change_title(session_id, new_title)
    return result

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
