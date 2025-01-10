from fastapi import FastAPI, HTTPException
from starlette.responses import StreamingResponse
from pydantic import BaseModel
import llamainference
import llamainferenceNBCE
import torch
from transformers import AutoTokenizer
from transformers import LlamaForCausalLM, AutoModelForCausalLM, BitsAndBytesConfig
from transformers import TopPLogitsWarper, LogitsProcessorList
from settings import *


bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)
def init_model(model_path = '../openbuddy-zephyr-7b-v14.1', peft_model=None):
    # 经过微调的LLAMA
    # 下载地址：https://openbuddy.ai/

    # 加载tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.padding_side = 'left' 
    tokenizer.pad_token = tokenizer.eos_token

    # 加载LLAMA模型
    model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    use_auth_token=True,
    max_length=MAX_TOKENS
    )
    if peft_model is not None:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, peft_model)

    return tokenizer, model

# 创建FastAPI实例
app = FastAPI()
tokenizer, model = init_model(model_path=get_llm_model(), peft_model=get_peft_model())

# 创建一个Pydantic模型，用于定义预期的请求体
class Item(BaseModel):
    model: str = "llama2"
    prompt: str = None
    system: str = None
    stream: bool = False
    context = []

# 创建一个POST方法的路由
@app.post("/api/generate")
async def generate(item: Item):
    text = item.system + item.prompt
    tokens = tokenizer.encode(text)
    if item.stream:
        if len(tokens) > 4000:
            return StreamingResponse(llamainferenceNBCE.streaming_generate_text(item.system, item.prompt, tokenizer, model), media_type='application/json')
        else:
            return StreamingResponse(llamainference.streaming_generate(item.prompt, item.system, tokenizer, model), media_type='application/json')
    else:
        output = {}
        if len(tokens) > 4000:
            text, tokens = llamainferenceNBCE.generate_text(item.system, item.prompt, tokenizer, model)
        else:
            text, tokens = llamainference.summarize_hf(item.prompt, item.system, tokenizer, model)
        output['response'] = text[0]
        output['context'] = tokens[0]
    return output

# 如果你想运行这个示例，请确保你的终端或命令行界面当前目录是这个脚本所在的目录
# 然后运行以下命令来启动Uvicorn服务器：
# uvicorn main:app --reload



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)

