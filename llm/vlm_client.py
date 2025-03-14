#import aiofiles
import base64
import asyncio
import io

import requests
from openai import OpenAI
from settings import MULTIMODAL_API_KEY, MULTIMODAL_BASE_URL, VLM_MAX_TOKEN, MULTIMODAL_MODEL_NAME

from fastapi import FastAPI, File, UploadFile, Form, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from mimetypes import guess_type
from concurrent.futures import ThreadPoolExecutor

#dependency of resize and is_proper_size
from PIL import Image
import math
from transformers import AutoTokenizer
from transformers import AutoProcessor



tpath = os.path.join(os.path.dirname(__file__), "tokenizer")
print(tpath)
tokenizer = AutoTokenizer.from_pretrained(tpath)

class VLMClient:
    def __init__(self):
        openai_api_key = MULTIMODAL_API_KEY
        openai_api_base = MULTIMODAL_BASE_URL
        self.client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
        )
        if MULTIMODAL_MODEL_NAME is None:
            models = self.client.models.list()
            self.model = models.data[0].id
        else:
            self.model = MULTIMODAL_MODEL_NAME
        self.executor = ThreadPoolExecutor(max_workers=None)  # 可以根据需要调整最大线程数

    def run_chart(self):
        #find bb
        #for every img ,run infer
        #return result and image array
        pass

    def run_single_image(self,image_url,state):

        # Open an image
        img = Image.open(image_url)  # Replace with your image file path
        return self.run_single_image_obj(img, state)

    def run_single_image_obj(self, img, state):
        file_format = img.format.lower()
        img=self.is_proper_size(img,state)
        # Create a BytesIO object
        byte_stream = io.BytesIO()
        # Save the image to the BytesIO object
        img.save(byte_stream, format=file_format)  # Specify the format (e.g., 'JPEG', 'PNG')
        # Retrieve the binary data
        byte_stream.seek(0)  # Reset the pointer to the start of the stream
        binary_data = byte_stream.getvalue()
        image_base64 = base64.b64encode(binary_data).decode('utf-8')
        # Print or use the binary data
        print(f"Binary data length: {len(binary_data)}")   
        ## Use base64 encoded image in the payload
        #image_base64 = encode_base64_content_from_url(image_url)
        chat_completion_from_base64 = self.client.chat.completions.create(
                    messages=[{
                        "role":
                        "user",
                        "content": [
                            {
                                "type": "text",
                                "text": state
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }],
                    model=self.model,
                    temperature=0.01,
                    top_p=0.01
        )
        result = chat_completion_from_base64.choices[0].message.content

        return result
    ## img: from PIL import Image.open, source image 
    ## prompt: str, used to calculate the token size that is used
    def is_proper_size( self,img,prompt):
        encoded_input = tokenizer.encode(prompt)## openai tokenizer 
        print("prompt的token长度:",len(encoded_input))
        ##print(encoded_input)
        width, height = img.size
        if math.ceil(height/28)*math.ceil(width/28)+2+17<VLM_MAX_TOKEN-len(encoded_input)-6:
            return img
        else: 
            return  self.resize(img,height,width,encoded_input) ## if the image out of size, do funtion resize() to resize the image
    ##img: from PIL import Image.open, source image , height: image height, width: image width.
    ## encoded_input: tokenS used by prompt
    def resize( self,img,height, width,encoded_input):
        print("resize img")
        print("原始图片大小：")
        print(math.ceil(float(height)))
        print(math.ceil(float(width)))
        info= height/width
        while math.ceil(height/28)*math.ceil(width/28)+2+17>=VLM_MAX_TOKEN-len(encoded_input)-6:
            height=height-info
            width=width-1
        print("修改后图片大小：")
        print(height)
        print(width)
        img1 =img.resize((width,int(height)))
        ##encoded_input = PEOCESSOR(images=img1,text="") ## if you want to debug, you can se the token that image used.
        ##print(encoded_input)
        return img1
    
def get_answer(file_location: str, prompt_name: str, current_language: str):
    # 判断图片大小
    vllm1 = VLMClient()
    prompt = ""
    print("获得到的prompt_name是",prompt_name)
    print("多模态获得到的语言是",current_language)

    if not prompt_name:
        if current_language == "zh-CN":
            from sysprompts import MUILT_MODEL_CN
            prompt = MUILT_MODEL_CN
        else:
            from sysprompts import MUILT_MODEL_EN
            prompt = MUILT_MODEL_EN

    else:
        prompt = user_prompt_info.get_prompt_content(prompt_name)
    # print("prompt的内容是:",prompt)
    print("正在处理的图片地址是：",file_location)
    result = vllm1.run_single_image(file_location, prompt)
    print("多模态的回复:")
    print(result)
    return result

if __name__ == "__main__":
    import sys
    from db import user_prompt_info
    answer = get_answer(sys.argv[1])
    print(answer)
