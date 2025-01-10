from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import time
from typing import Optional
import numpy as np
import tempfile

app = FastAPI()
# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，或者你可以指定来源 ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

DATA_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


import pypdfium2 # Needs to be at the top to avoid warnings
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1" # For some reason, transformers decided to use .isin for a simple op, which is not supported on MPS

from marker.convert import convert_single_pdf
from marker.logger import configure_logging
from marker.models import load_all_models

from marker.output import save_markdown

configure_logging()
model_lst = load_all_models()

def inference(fname, max_pages=None, start_page=None, langs=None, batch_multiplier=2, debug=True):

    start = time.time()
    full_text, images, out_meta = convert_single_pdf(fname, model_lst, max_pages=max_pages, langs=langs, batch_multiplier=batch_multiplier, start_page=start_page)

    if debug:
        print(f"Total time: {time.time() - start}")

    return full_text

@app.post("/api/generate")
async def generate(file: UploadFile = File(...)):
    filename = os.path.join(tempfile.gettempdir(), f'{time.time()}{file.filename}')
    print(file.filename)
    print(file.content_type)
    data = file.file.read()
    print(len(data))
    with open(file=filename, mode='wb') as fp:
        fp.write(data)

    text = inference(filename)
    return {"text": text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
