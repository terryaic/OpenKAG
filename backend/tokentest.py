#! -*- coding: utf-8 -*-
# Naive Bayes-based Context Extension (NBCE)
# 使用朴素贝叶斯增加LLM的Context处理长度
# 链接：https://kexue.fm/archives/9617
# Torch 2.0 测试通过

import json
import torch
from transformers import AutoTokenizer
from transformers import LlamaForCausalLM
from transformers import TopPLogitsWarper, LogitsProcessorList

# 经过微调的LLAMA
# 下载地址：https://openbuddy.ai/
model_path = '../openbuddy-zephyr-7b-v14.1'

# 加载tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path)
tokenizer.padding_side = 'left' 
tokenizer.pad_token = tokenizer.unk_token


if __name__ == "__main__":
    import sys
    # 使用示例
    filename = 'your_text_file.txt'  # 替换为您的文件名
    filename = sys.argv[1]
    
    # 读取文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()

    line_encoded = tokenizer(text,
                                return_tensors='pt',
                                padding=True,
                                truncation=True)["input_ids"].type(torch.int64)
    print(line_encoded.shape)