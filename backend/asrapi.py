from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse,JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import time
from typing import Optional
import numpy as np
import soundfile
import whisper
import tempfile
from settings import WHISPERMODEL_SIZE,ASR_PORT
app = FastAPI()
# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，或者你可以指定来源 ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)
model = whisper.load_model(WHISPERMODEL_SIZE)

DATA_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@app.post("/api/generate")
async def generate(file: UploadFile = File(...)):
    filename = os.path.join(tempfile.gettempdir(), f'{time.time()}{file.filename}')
    print(file.filename)
    print(file.content_type)
    audio = file.file.read()
    print(len(audio))
    with open(file=filename, mode='wb') as fp:
        fp.write(audio)

    #return inference_asr(filename)
    return transcribe_audio_whisper(filename)
    """
    memory_file = io.BytesIO()
    memory_file.name = file.filename
    memory_file.write(audio)
    memory_file.seek(0)
    audio_data, sr = soundfile.read(memory_file, dtype=np.float32)
    return inference(audio_data)
    """

def inference_asr(file):
    audio = whisper.load_audio(file)
    return inference(audio)

def inference(audio):
    # load audio and pad/trim it to fit 30 seconds
    #audio = whisper.load_audio("audio.mp3")
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)

    # print the recognized text
    print(result.text)
    return result

def transcribe_audio_whisper(path):
    result = model.transcribe(path, initial_prompt="以下是普通话的句子。")
    print(result['text'])
    return result

@app.post("/api/generate_path")
async def generate_path(data: dict):
    """
    接收包含文件路径的字典，转录指定的音频文件
    """
    file_path = data.get("audio")

    if not file_path:
        raise HTTPException(status_code=400, detail="File path is required")

    # 检查文件路径是否存在
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        # 调用转录函数
        transcription = transcribe_audio_whisper(file_path)

        # 返回 JSON 格式的转录文本
        return transcription

    except Exception as e:
        # 捕获异常并返回错误信息
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=ASR_PORT)
