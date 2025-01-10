
import requests
from requests_toolbelt import MultipartEncoder
import os
import json

def get_mimetype(str1):
    name = str1.lower()
    if name.endswith("png"):
        return "image/png"
    elif name.endswith("jpg") or name.lower().endswith("jpeg"):
        return "image/jpeg"
    elif name.endswith("zip"):
        return "application/zip"
    elif name.endswith(".mp3"):
        return "audio/mpeg-3"
    elif name.endswith(".pdf"):
        return "application/pdf"
    else:
        return "application/binary"
    
def upload_file(in_file, url, authorization=None):
    print(f'upload {in_file} to:{url}')
    if len(in_file) == 1:
        filename = os.path.basename(in_file[0])
        with open(in_file[0], 'rb') as fp:
            fs = fp.read()
        m = MultipartEncoder(
                fields={
                    'file': (filename, fs, get_mimetype(filename))
                }
            )
    try:
        r = requests.post(url, data=m,
        headers={'Content-Type': m.content_type,'Authorization':authorization})
        if r.status_code == 200:
            print(r.content.decode("utf8"))
            if r.headers['content-type'] == "application/json":
                text = r.content.decode("utf8")
                obj = json.loads(text)
                return obj
        else:
            print(f"uplaod failed:{r.status_code}")
    except Exception as e:
        print(e)
    return None


def audio_file_process(filepath: str, url: str):

    # 否则，发送文件路径作为字符串到 API
    data = {'audio': filepath}
    response = requests.post(url, json=data)

    # 检查返回结果
    if response.status_code == 200:
        # 如果请求成功，返回转录的文本
        data = response.json()
        transcription = data.get("text", "")
        return transcription
    else:
        # 如果发生错误，返回错误信息
        raise Exception(f"Error: {response.status_code}, {response.text}")