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
import ChatTTS
import torch
import torchaudio

chat = ChatTTS.Chat()
chat.load(compile=False) # Set to True for better performance

texts = ["PUT YOUR 1st TEXT HERE", "PUT YOUR 2nd TEXT HERE"]

wavs = chat.infer(texts)
print(wavs[0].shape)
print(len(wavs[0]))
#torchaudio.save("output1.wav", torch.from_numpy(wavs[0]), 24000)

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

import torch


class TorchSeedContext:
    def __init__(self, seed):
        self.seed = seed
        self.state = None

    def __enter__(self):
        self.state = torch.random.get_rng_state()
        torch.manual_seed(self.seed)

    def __exit__(self, type, value, traceback):
        torch.random.set_rng_state(self.state)


audio_seed_input = 2
with TorchSeedContext(audio_seed_input):
    rand_spk = chat.sample_random_speaker()

@app.post("/api/generate")
async def generate(content: str = Form(...), language: Optional[str] = Form(default=None)):
    print(content, language)

    params_infer_code = ChatTTS.Chat.InferCodeParams(
        spk_emb = rand_spk, # add sampled speaker 
        temperature = .3,   # using custom temperature
        top_P = 0.7,        # top P decode
        top_K = 20,         # top K decode
    )

    ###################################
    # For sentence level manual control.

    # use oral_(0-9), laugh_(0-2), break_(0-7) 
    # to generate special token in text to synthesize.
    params_refine_text = ChatTTS.Chat.RefineTextParams(
        prompt='[oral_2][laugh_0][break_6]',
    )

    wav = chat.infer(
        content,
        params_refine_text=params_refine_text,
        params_infer_code=params_infer_code,
    )
    print(wav)

    import soundfile as sf
    import io

    sample_rate = 24000 

    # Create a BytesIO object to hold the audio data in memory
    memory_file = io.BytesIO()

    # Write the audio data to the in-memory file
    sf.write(memory_file, wav[0].tolist(), sample_rate, format='WAV')

    # To use the audio data, you can seek back to the beginning of the in-memory file
    memory_file.seek(0)
    # 创建 StreamingResponse，返回二进制内容
    return StreamingResponse(memory_file, media_type="audio/x-wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)

