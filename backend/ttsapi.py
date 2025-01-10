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
from TTS.api import TTS
#import xtts
USING_XTTS_V2 = True
DATA_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SPEAKER_WAV = os.path.join(DATA_DIR, "speaker.wav")

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"
if USING_XTTS_V2:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    wav = tts.tts(text="Hello world!", speaker_wav=SPEAKER_WAV, language="en")
else:
    tts_cn = TTS("tts_models/zh-CN/baker/tacotron2-DDC-GST").to(device)
    tts_en = TTS("tts_models/en/ljspeech/tacotron2-DDC").to(device)
#tts = TTS("tts_models/multilingual/multi-dataset/xtts_v1.1").to(device)
#tts = TTS("tts_models/multilingual/multi-dataset/your_tts").to(device)
#tts = TTS("../XTTS-v2").to(device)

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
async def generate(content: str = Form(...), language: Optional[str] = Form(default=None)):
    print(content, language)
    wav = None
    if content in wav_cache.keys():
        while wav is None:
            wav = wav_cache[content]
            if wav is None:
                time.sleep(0.01)
        wav_cache.pop(content)
    else:
        if USING_XTTS_V2:
            if language is None:
                wav = tts.tts(text = content, speaker_wav=SPEAKER_WAV, language='zh-cn') #tts.tts(text = content, speaker_wav=SPEAKER_WAV, language='zh-CN')
            elif language.startswith('zh'):
                wav = tts.tts(text = content, speaker_wav=SPEAKER_WAV, language='zh-cn')
            elif language == 'en':
                wav = tts.tts(text = content, speaker_wav=SPEAKER_WAV, language='en')
            else:
                wav = tts.tts(text = content, speaker_wav=SPEAKER_WAV, language='zh-cn')

        else:
            if language is None:
                #wav = xtts.inference(text = content, speaker_wav=SPEAKER_WAV, language='zh-cn') #tts.tts(text = content, speaker_wav=SPEAKER_WAV, language='zh-CN')
                wav = tts_cn.tts(text = content)
            elif language.startswith('zh'):
                #wav = xtts.inference(text = content, speaker_wav=SPEAKER_WAV, language=language)
                wav = tts_cn.tts(text = content)
            elif language == 'en':
                #wav = xtts.inference(text = content, speaker_wav=SPEAKER_WAV, language=language)
                wav = tts_en.tts(text = content)
            else:
                #wav = xtts.inference(text = content, speaker_wav=SPEAKER_WAV, language='zh-cn')
                wav = tts_cn.tts(text = content)
        print(len(wav))
        wav_cache[content] = wav

    #speech = np.asarray(wav) * 32768
    #data16 = speech.astype(np.int16)

    import soundfile as sf
    import io

    sample_rate = 22050 

    # Create a BytesIO object to hold the audio data in memory
    memory_file = io.BytesIO()

    # Write the audio data to the in-memory file
    sf.write(memory_file, wav, sample_rate, format='WAV')

    # To use the audio data, you can seek back to the beginning of the in-memory file
    memory_file.seek(0)
    # 创建 StreamingResponse，返回二进制内容
    return StreamingResponse(memory_file, media_type="audio/x-wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)

