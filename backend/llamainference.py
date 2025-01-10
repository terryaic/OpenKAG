import numpy as np
import copy
import torch
from transformers import AutoTokenizer
from transformers import LlamaForCausalLM
from transformers import AutoModelForCausalLM, LlamaTokenizer
from transformers import TextIteratorStreamer
from threading import Thread
import json
from prompts import get_prompt

max_token_num = 2048

def init_model(hf_model_location = "../llama-recipes/models/7b-Instruct"):
    tokenizer = AutoTokenizer.from_pretrained(hf_model_location,
                                                legacy=False,
                                                padding_side='left')
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(hf_model_location, load_in_8bit=True, device_map= 'auto', low_cpu_mem_usage=True)
    model.eval()
    #model.half()
    #model.cuda()
    return tokenizer, model

def summarize_hf(user_message, system_prompt, tokenizer, model, temperature=1, output_len = 1000, top_k=1, num_beams=1):
    prompt_template = get_prompt(model.name_or_path)
    text = prompt_template.replace("*system_prompt*", system_prompt).replace("*user_message*", user_message) 
    line_encoded = tokenizer(text,
                                return_tensors='pt',
                                padding=True,
                                truncation=True)["input_ids"].type(torch.int64)

    #line_encoded = line_encoded[:, -max_token_num:]
    line_encoded = line_encoded.cuda()

    with torch.no_grad():
        output = model.generate(line_encoded,
                                max_length=len(line_encoded[0]) +
                                output_len,
                                top_k=top_k,
                                temperature=temperature,
                                eos_token_id=tokenizer.eos_token_id,
                                pad_token_id=tokenizer.pad_token_id,
                                num_beams=num_beams,
                                num_return_sequences=num_beams,
                                use_cache=True,
                                early_stopping=True)

    tokens_list = output[:, len(line_encoded[0]):].tolist()
    output = output.reshape([1, num_beams, -1])
    output_lines_list = tokenizer.batch_decode(output[:, 0, len(line_encoded[0]):],
                                skip_special_tokens=True)

    return output_lines_list, tokens_list

async def streaming_generate(user_message, system_prompt, tokenizer, model, temperature=1, output_len = 1000, top_k=1, num_beams=1):
    prompt_template = get_prompt(model.name_or_path)
    text = prompt_template.replace("*system_prompt*", system_prompt).replace("*user_message*", user_message) 
    line_encoded = tokenizer(text,
                                return_tensors='pt',
                                padding=True,
                                truncation=True)["input_ids"].type(torch.int64)

    #line_encoded = line_encoded[:, -max_token_num:]
    line_encoded = line_encoded.cuda()

    streamer = TextIteratorStreamer(tokenizer)
    # Run the generation in a separate thread, so that we can fetch the generated text in a non-blocking way.
    generation_kwargs = dict(inputs=line_encoded, streamer=streamer,
                                max_length=len(line_encoded[0]) +
                                output_len,
                                top_k=top_k,
                                temperature=temperature,
                                eos_token_id=tokenizer.eos_token_id,
                                pad_token_id=tokenizer.pad_token_id,
                                num_beams=num_beams,
                                num_return_sequences=num_beams,
                                early_stopping=True)
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    starting = True
    for new_text in streamer:
        print(new_text, flush=True, end='')
        if starting:
            pass
        elif new_text == '</s>':
            msg = json.dumps({'response': '', 'done': True}) + "\n"
            yield msg
        else:
            msg = json.dumps({'response': new_text}) + "\n"
            yield msg
        if new_text.find("Assistant:")>=0:
            starting = False

if __name__ == "__main__":
    import sys
    import time
    # 使用示例
    filename = 'your_text_file.txt'  # 替换为您的文件名
    question = "本文介绍的是什么？"
    filename = sys.argv[1]
    if len(sys.argv) > 2:
        model = sys.argv[2]
    
    # 读取文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()

    tk, md = init_model(model)

    t1 = time.time()

    output, tokens = summarize_hf(question, text, tk, md)
    print(output)
    print(tokens)

    t2 = time.time()
    print(f"time cost:{t2-t1}")
    print(f"text len:{len(text)}, output token len:{len(tokens[0])}")

