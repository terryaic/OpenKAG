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
from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"
model = "models/CosyVoice-300M-SFT"

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
    prompt: Optional[str] = Form(default="")
):
    print(content, language)
    cosyvoice = CosyVoice(model)
    # instruct usage, support <laughter></laughter><strong></strong>[laughter][breath]
    #output = cosyvoice.inference_instruct(content, voice_tone, prompt)
    output = cosyvoice.inference_sft(content, voice_tone)
    print(output['tts_speech'].shape)
    wav = output['tts_speech'].tolist()[0]

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

