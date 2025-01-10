#! -*- coding: utf-8 -*-
import requests
import json
from settings import get_llm_url,get_llm_model,get_api_type,API_OPENAI,MAX_TOKENS,TEMPERATURE
from streamprocess import StreamProcess

def get_prompt(sourcetext, mode=None):
    if mode=='chat':
        systemPrompt = ""
    else:
        systemPrompt = f"Only use the following information to answer the question and provide the images if possible. Do not use anything else, if there is any http link, return it as this format <http://>: {sourcetext}"
    if mode == 'code':
        systemPrompt += "\n\n. You are in Omniverse scene. suppose the up axis is Y. don't define any function and only generate the code. code should be included within '''. and only generate one answer. \n Question: write python code to "
    print(f'systemPrompt:{systemPrompt}')
    print(f'systemPrompt len:{len(systemPrompt)}')
    return systemPrompt

async def streamquery(question, callback, sourcetext, mode=None, context = []):
    print("streamquery:%s"%question)
    code_mode = False

    url = get_llm_url()

    if get_api_type() == API_OPENAI:
        payload = {
        "model": get_llm_model(),
        "prompt":get_prompt(sourcetext, mode) + question,
        "stream": True,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE 
        }
    else:
        payload = {
        "model": get_llm_model(),#"mistral-openorca",
        "prompt": question, 
        "system": sourcetext,
        "stream": True,
        "context": context
    }

    # Convert the payload to a JSON string
    payload_json = json.dumps(payload)

    # Set the headers to specify JSON content
    headers = {
        "Content-Type": "application/json"
    }

    proc = StreamProcess()
    # Send the POST request
    r = requests.post(url, data=payload_json, headers=headers,
                      stream=True)
    r.raise_for_status()
    if code_mode:
        await callback("", text_type='code_begin')

    for line in r.iter_lines():
        print(line)
        if get_api_type() == API_OPENAI:
            line = line.decode("utf8")
            #print(line)
            if line.startswith("data:"):
                line = line[5:]
            line = line.strip()
            if line.startswith("[DONE"):
                break
            if not line.startswith("{"):
                continue
            body = json.loads(line.strip())
            response_part = body.get("choices")[0]['text']
        else:
            body = json.loads(line)
            response_part = body.get('response', '')
            
        if code_mode:
            await callback(response_part, text_type='code_continue')
            continue

        await proc.process_chat(response_part, callback=callback)

        if 'error' in body:
            raise Exception(body['error'])

        if body.get('done', False):
            break
    if code_mode:
        await callback(proc.code, text_type='code_end')
    else:
        await callback(proc.text)

def query(question, callback, sourcetext, mode=None, context = []):
    print("query:%s"%question)
    code_mode = False

    url = get_llm_url()

    if get_api_type() == API_OPENAI:
        payload = {
        "model": get_llm_model(),
        "prompt":get_prompt(sourcetext, mode) + question,
        "stream": True,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE 
        }
    else:
        payload = {
        "model": get_llm_model(),#"mistral-openorca",
        "prompt": question, 
        "system": sourcetext,
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
    if code_mode:
        callback("", text_type='code_begin')

    for line in r.iter_lines():
        if get_api_type() == API_OPENAI:
            line = line.decode("utf8")
            #print(line)
            if line.startswith("data:"):
                line = line[5:]
            line = line.strip()
            if line.startswith("[DONE"):
                break
            if not line.startswith("{"):
                continue
            body = json.loads(line.strip())
            response_part = body.get("choices")[0]['text']
        else:
            body = json.loads(line)
            response_part = body.get('response', '')
            
        if code_mode:
            callback(response_part, text_type='code_continue')
            continue

        callback(response_part, text_type='char')

        if 'error' in body:
            raise Exception(body['error'])

        if body.get('done', False):
            break

def chat(question, callback, sourcetext, mode=None):
    print("chat:%s"%question)
    code_mode = False

    url = get_llm_url()

    if get_api_type() == API_OPENAI:
        payload = {
        "model": get_llm_model(),
        "prompt":get_prompt(sourcetext, mode) + question,
        "stream": True,
        "max_self.tokens": MAX_TOKENS,
        "temperature": TEMPERATURE 
        }
    else:
        payload = {
        "model": get_llm_model(),
        "messages": [
            {
            "role": "user",
            "content": question
            }
        ],
        "stream": True
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
    if code_mode:
        callback("", text_type='code_begin')

    for line in r.iter_lines():
        if get_api_type() == API_OPENAI:
            line = line.decode("utf8")
            #print(line)
            if line.startswith("data:"):
                line = line[5:]
            line = line.strip()
            if line.startswith("[DONE"):
                break
            if not line.startswith("{"):
                continue
            body = json.loads(line.strip())
            response_part = body.get("choices")[0]['text']
        else:
            body = json.loads(line)
            response_part = body.get('message', {}).get("content","")
            
        if code_mode:
            callback(response_part, text_type='code_continue')
            continue

        callback(response_part, text_type='char')

        if 'error' in body:
            raise Exception(body['error'])

        if body.get('done', False):
            break
