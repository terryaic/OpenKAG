from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import time
from typing import Optional
import numpy as np
import struct
import torch
DATA_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SPEAKER_WAV = os.path.join(DATA_DIR, "speaker.wav")
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id_cantonese = 'speech_tts/speech_sambert-hifigan_tts_jiajia_Cantonese_16k'
model_id_mandarin = 'speech_tts/speech_sambert-hifigan_tts_zh-cn_multisp_pretrain_16k'

text = '待合成文本'
sambert_hifigan_tts_cantonese = pipeline(task=Tasks.text_to_speech, model=model_id_cantonese)
output = sambert_hifigan_tts_cantonese(input=text)
wav = output[OutputKeys.OUTPUT_WAV]

sambert_hifigan_tts_mandarin = pipeline(task=Tasks.text_to_speech, model=model_id_mandarin)
output = sambert_hifigan_tts_mandarin(input=text)
wav = output[OutputKeys.OUTPUT_WAV]

app = FastAPI()
# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，或者你可以指定来源 ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

wav_cache = {}

@app.post("/api/generate")
async def generate(content: str = Form(...), 
    language: Optional[str] = Form(default=None),
    voice_tone: Optional[str] = Form(default="中文女"),
    prompt: Optional[str] = Form(default=""),
    locale: Optional[str] = Form(default="mandarin")
):
    print(content, language, locale)
    start_time = time.time()
    if locale == 'cantonese':
        output = sambert_hifigan_tts_cantonese(input=content)
    else:
        output = sambert_hifigan_tts_mandarin(input=content)
    end_time = time.time()
    print(f"{end_time-start_time}")

    wav = output[OutputKeys.OUTPUT_WAV]

    import io
    # Create a BytesIO object to hold the audio data in memory
    memory_file = io.BytesIO()
    memory_file.write(wav)

    # To use the audio data, you can seek back to the beginning of the in-memory file
    memory_file.seek(0)
    # 创建 StreamingResponse，返回二进制内容
    return StreamingResponse(memory_file, media_type="audio/x-wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)

