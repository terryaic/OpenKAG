#! -*- coding: utf-8 -*-
# Naive Bayes-based Context Extension (NBCE)
# 使用朴素贝叶斯增加LLM的Context处理长度
# 链接：https://kexue.fm/archives/9617
# Torch 2.0 测试通过

import json
import torch
from transformers import AutoTokenizer
from transformers import LlamaForCausalLM,AutoModelForCausalLM
from transformers import TopPLogitsWarper, LogitsProcessorList


def init_model(model_path = '../openbuddy-zephyr-7b-v14.1'):
    # 经过微调的LLAMA
    # 下载地址：https://openbuddy.ai/

    # 加载tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.padding_side = 'left' 
    tokenizer.pad_token = tokenizer.unk_token

    # 加载LLAMA模型
    model = AutoModelForCausalLM.from_pretrained(model_path, load_in_4bit=True, device_map="auto")
    return tokenizer, model

device = torch.device('cuda')

# Top-P截断
processors = LogitsProcessorList()
processors.append(TopPLogitsWarper(0.95))


def generate_text(text, question, tokenizer, model):
    from utils import split_text
    from prompts import get_format
    contexts = split_text(text, model_name = model.name_or_path)
    batch = [ get_format(model.name_or_path) % (context, question) for context in contexts]
    return generate(batch, 1000, tokenizer, model)

@torch.inference_mode()
def generate(batch, max_tokens, tokenizer, model):
    """Naive Bayes-based Context Extension 演示代码
    """
    text = ""
    tokens = []
    inputs = tokenizer(batch, padding='longest', return_tensors='pt').to(device)
    input_ids = inputs.input_ids
    attention_mask = inputs.attention_mask
    
    print('input_ids', input_ids.shape)
    past_key_values = None
    n = input_ids.shape[0]
    
    t0 = time.time()
    latency = None
    for i in range(max_tokens):
        # 模型输出
        outputs = model(input_ids=input_ids,
                        attention_mask=attention_mask,
                        return_dict=True,
                        use_cache=True,
                        past_key_values=past_key_values
                       )
        past_key_values = outputs.past_key_values
        
        # ===== 核心代码开始 =====
        beta, eta = 0.25, 0.1
        logits = outputs.logits[:, -1]
        logits = logits - logits.logsumexp(dim=-1, keepdims=True)
        logits = processors(input_ids, logits)
        entropy = -(logits.exp() * logits.clip(-100, 0)).sum(dim=-1)
        if i > 0:
            entropy[k] -= eta
        k = entropy[1:].argmin() + 1
        logits_max = logits[k]
        logits_uncond = logits[0]
        logits_merged = (1 + beta) * logits_max - beta * logits_uncond
        logits = torch.where(logits_uncond > -100, logits_merged, logits_max)
        # ===== 核心代码结束 =====
        
        # 构建分布，采样
        # tau = 1是标准的随机采样，tau->0则是贪心搜索
        # 简单起见，这里没有实现topk、topp截断
        tau = 0.01
        probas = torch.nn.functional.softmax(logits[None] / tau , dim=-1)
        next_tokens = torch.multinomial(probas, num_samples=1).squeeze(1)        
        if next_tokens[0] == tokenizer.eos_token_id:
            break
            
        ret = tokenizer.batch_decode(next_tokens)
        text += ret[0]
        tokens.append(next_tokens[0])
        if latency is None:
            latency = time.time() - t0
        #print(ret[0], flush=True, end='')
        #print(tokenizer.decode(tokens), flush=True)
        
        # prepare for next iteration
        input_ids = next_tokens.unsqueeze(-1).tile(n, 1)
        attention_mask = torch.cat([attention_mask, torch.ones(n, 1, dtype=torch.long, device=device)], dim=-1)        
    print(f"latency:{latency}")
    return text, tokens

async def streaming_generate_text(text, question, tokenizer, model,max_tokens=1000):
    from utils import split_text
    from prompts import get_format
    contexts = split_text(text, model_name = model.name_or_path)
    batch = [ get_format(model.name_or_path) % (context, question) for context in contexts]
    
    """Naive Bayes-based Context Extension 演示代码
    """
    text = ""
    tokens = []
    inputs = tokenizer(batch, padding='longest', return_tensors='pt').to(device)
    input_ids = inputs.input_ids
    attention_mask = inputs.attention_mask
    
    print('input_ids', input_ids.shape)
    past_key_values = None
    n = input_ids.shape[0]
    
    last_res = ''
    with torch.no_grad():
      for i in range(max_tokens):
        # 模型输出
        outputs = model(input_ids=input_ids,
                        attention_mask=attention_mask,
                        return_dict=True,
                        use_cache=True,
                        past_key_values=past_key_values
                       )
        past_key_values = outputs.past_key_values
        
        # ===== 核心代码开始 =====
        beta, eta = 0.25, 0.1
        logits = outputs.logits[:, -1]
        logits = logits - logits.logsumexp(dim=-1, keepdims=True)
        logits = processors(input_ids, logits)
        entropy = -(logits.exp() * logits.clip(-100, 0)).sum(dim=-1)
        if i > 0:
            entropy[k] -= eta
        k = entropy[1:].argmin() + 1
        logits_max = logits[k]
        logits_uncond = logits[0]
        logits_merged = (1 + beta) * logits_max - beta * logits_uncond
        logits = torch.where(logits_uncond > -100, logits_merged, logits_max)
        # ===== 核心代码结束 =====
        
        # 构建分布，采样
        # tau = 1是标准的随机采样，tau->0则是贪心搜索
        # 简单起见，这里没有实现topk、topp截断
        tau = 0.01
        probas = torch.nn.functional.softmax(logits[None] / tau , dim=-1)
        next_tokens = torch.multinomial(probas, num_samples=1).squeeze(1)        
        if next_tokens[0] == tokenizer.eos_token_id:
            break
            
        ret = tokenizer.batch_decode(next_tokens)
        text += ret[0]
        tokens.append(next_tokens[0])
        print(ret[0], flush=True, end='')
        res = tokenizer.decode(tokens)
        itertext = res[len(last_res):]
        last_res = res
        msg = json.dumps({'response': itertext}) + "\n"
        yield msg
        
        # prepare for next iteration
        input_ids = next_tokens.unsqueeze(-1).tile(n, 1)
        attention_mask = torch.cat([attention_mask, torch.ones(n, 1, dtype=torch.long, device=device)], dim=-1)        


MAX_INPUT_LENGTH=500
async def streaming_generate_text2(text, question, tokenizer, model,max_tokens=1000, max_batch_size=1):
    import gc
    from utils import split_text
    from prompts import get_format
    print(text)
    contexts = split_text(text, model_name = model.name_or_path, max_length=MAX_INPUT_LENGTH)
    batch = [ get_format(model.name_or_path) % (context, question) for context in contexts]
    question_tokens = tokenizer(question)
    max_length = MAX_INPUT_LENGTH + len(question_tokens.input_ids) + 10

    """Naive Bayes-based Context Extension 演示代码
    """
    text = ""
    tokens = []
    
    past_key_values = None
    n = len(batch)

    logits = []
    masks = []
    pk = []
    for i in range(32):
        pk.append([])
    current_batch = 0
    use_cache = True
    with torch.no_grad():
        while current_batch < n:
            inputs = tokenizer(batch[current_batch: current_batch+max_batch_size], padding='max_length', max_length=max_length, return_tensors='pt').to(device)
            input_ids = inputs.input_ids
            print(f'input shape:{input_ids.shape}')
            attention_mask = inputs.attention_mask
            current_outputs = model(input_ids=input_ids, 
                            attention_mask=attention_mask,
                            return_dict=True,
                            use_cache=use_cache,
                            past_key_values=past_key_values
                        )
            masks.append(inputs.attention_mask.cpu())
            logits.append(current_outputs.logits.cpu()[:, -1])
            #pk.append(current_outputs.past_key_values.cpu())
            current_batch += max_batch_size
            if use_cache:
                print(f'kv:{len(current_outputs.past_key_values)}')
                for i in range(len(current_outputs.past_key_values)):
                    for j in range(len(current_outputs.past_key_values[i])):
                        #del current_outputs.past_key_values[i][j]
                        pk[i].append(current_outputs.past_key_values[i][j].cpu())
            """
            del input_ids
            del attention_mask
            del inputs
            del current_outputs
            gc.collect()
            torch.cuda.empty_cache()
            """

        past_key_values = tuple(tuple(tensor.to('cuda') for tensor in inner_list) for inner_list in pk)
        logits = torch.cat(logits, dim=0).cuda()
        attention_mask = torch.cat(masks, dim=0).cuda()
        inputs = tokenizer(batch, padding='max_length', max_length=max_length,  return_tensors='pt').to(device)
        input_ids = inputs.input_ids

        print(f'input_ids:{input_ids.shape}')
        print(f'attention_mask:{attention_mask.shape}')
        print(f'logits:{logits.shape}')
        
        for i in range(max_tokens):
            
            # ===== 核心代码开始 =====
            beta, eta = 0.25, 0.1
            logits = logits - logits.logsumexp(dim=-1, keepdims=True)
            logits = processors(input_ids, logits)
            entropy = -(logits.exp() * logits.clip(-100, 0)).sum(dim=-1)
            if i > 0:
                entropy[k] -= eta
            k = entropy[1:].argmin() + 1
            logits_max = logits[k]
            logits_uncond = logits[0]
            logits_merged = (1 + beta) * logits_max - beta * logits_uncond
            logits = torch.where(logits_uncond > -100, logits_merged, logits_max)
            # ===== 核心代码结束 =====
            
            # 构建分布，采样
            # tau = 1是标准的随机采样，tau->0则是贪心搜索
            # 简单起见，这里没有实现topk、topp截断
            tau = 0.01
            probas = torch.nn.functional.softmax(logits[None] / tau , dim=-1)
            next_tokens = torch.multinomial(probas, num_samples=1).squeeze(1)        
            if next_tokens[0] == tokenizer.eos_token_id:
                break
                
            ret = tokenizer.batch_decode(next_tokens)
            text += ret[0]
            tokens.append(next_tokens[0])
            print(ret[0], flush=True, end='')
            msg = json.dumps({'response': ret[0]}) + "\n"
            yield msg
            
            # prepare for next iteration
            input_ids = next_tokens.unsqueeze(-1).tile(n, 1)
            attention_mask = torch.cat([attention_mask, torch.ones(n, 1, dtype=torch.long, device=device)], dim=-1)        
            # 模型输出
            outputs = model(input_ids=input_ids,
                            attention_mask=attention_mask,
                            return_dict=True,
                            use_cache=False,
                            past_key_values=past_key_values
                        )
            past_key_values = outputs.past_key_values
            logits = outputs.logits[:, -1]

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
    text, tokens = generate_text(text, question, tk, md)
    t2 = time.time()
    print(text)
    print(f"time cost:{t2-t1}")
    print(f"len:{len(text)}, token len:{tokens}")
