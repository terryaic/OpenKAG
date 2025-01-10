#! -*- coding: utf-8 -*-
from transformers import AutoTokenizer

def split_text(text, model_name='gpt2', max_length=1000):
    # 加载tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # 分割文本
    tokens = tokenizer.tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for token in tokens:
        current_chunk.append(token)
        current_length += 1

        # 当接近最大长度时，检查是否为句子结束
        if current_length >= max_length:
            # 寻找最近的句子结束符
            tt = tokenizer.convert_tokens_to_string(current_chunk)
            for i in range(len(current_chunk) - 1, 0, -1):
                if tt[i] in ['。', '！', '？', '!', '?', '.']:
                    next_chunk_start = i + 1
                    break
            else:
                # 如果没有找到句子结束符，使用最大长度
                next_chunk_start = max_length

            # 分割chunk并准备下一个
            chunk_text = tokenizer.convert_tokens_to_string(current_chunk[:next_chunk_start])
            chunks.append(chunk_text)
            current_chunk = current_chunk[next_chunk_start:]
            current_length = len(current_chunk)

    # 处理剩余的tokens
    if current_chunk:
        chunk_text = tokenizer.convert_tokens_to_string(current_chunk)
        chunks.append(chunk_text)

    return chunks


if __name__ == "__main__":
    import sys
    # 使用示例
    filename = 'your_text_file.txt'  # 替换为您的文件名
    filename = sys.argv[1]
    model_name = sys.argv[2]
    
    # 读取文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()

    chunks = split_text(text, model_name)

    # 打印分割后的文本块
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}:\n{len(chunk)}\n")
