
import argparse
import csv
import json
from pathlib import Path
import time
import numpy as np
import torch
from utils import (DEFAULT_HF_MODEL_DIRS, DEFAULT_PROMPT_TEMPLATES,
                   load_tokenizer, read_model_name, throttle_generator)

import tensorrt_llm
from tensorrt_llm.logger import logger
from tensorrt_llm.runtime import PYTHON_BINDINGS, ModelRunner

if PYTHON_BINDINGS:
    from tensorrt_llm.runtime import ModelRunnerCpp

from fastapi import FastAPI, HTTPException
from starlette.responses import StreamingResponse
from pydantic import BaseModel

prompt_template="""
<s>[INST] <<SYS>>
*system_prompt*
<</SYS>>
*user_message*
[/INST]
"""

# 创建FastAPI实例
app = FastAPI()

# 创建一个Pydantic模型，用于定义预期的请求体
class Item(BaseModel):
    model: str = "llama2"
    prompt: str = None
    system: str = None
    stream: bool = False

# 创建一个POST方法的路由
@app.post("/api/generate")
async def generate(item: Item):
    text = prompt_template.replace("*system_prompt*", item.system ).replace("*user_message*", item.prompt) 
    if item.stream:
        return StreamingResponse(inference(input_text=[text], streaming=True), media_type='application/json')
    else:
        output = {}
        text, tokens = inference(input_text=[text])
        output['response'] = text
    return output

# 如果你想运行这个示例，请确保你的终端或命令行界面当前目录是这个脚本所在的目录
# 然后运行以下命令来启动Uvicorn服务器：
# uvicorn main:app --reload





def parse_arguments(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--max_output_len', type=int, required=True)
    parser.add_argument(
        '--max_attention_window_size',
        type=int,
        default=None,
        help=
        'The attention window size that controls the sliding window attention / cyclic kv cache behaviour'
    )
    parser.add_argument('--log_level', type=str, default='error')
    parser.add_argument('--engine_dir', type=str, default='engine_outputs')
    parser.add_argument('--use_py_session',
                        default=False,
                        action='store_true',
                        help="Whether or not to use Python runtime session")
    parser.add_argument(
        '--input_text',
        type=str,
        nargs='+',
        default=["Born in north-east France, Soyer trained as a"])
    parser.add_argument(
        '--no_prompt_template',
        dest='use_prompt_template',
        default=True,
        action='store_false',
        help=
        "Whether or not to use default prompt template to wrap the input text.")
    parser.add_argument(
        '--input_file',
        type=str,
        help=
        'CSV or Numpy file containing tokenized input. Alternative to text input.',
        default=None)
    parser.add_argument('--max_input_length', type=int, default=923)
    parser.add_argument('--output_csv',
                        type=str,
                        help='CSV file where the tokenized output is stored.',
                        default=None)
    parser.add_argument('--output_npy',
                        type=str,
                        help='Numpy file where the tokenized output is stored.',
                        default=None)
    parser.add_argument(
        '--output_logits_npy',
        type=str,
        help=
        'Numpy file where the generation logits are stored. Use only when num_beams==1',
        default=None)
    parser.add_argument('--tokenizer_dir',
                        help="HF tokenizer config path",
                        default='gpt2')
    parser.add_argument(
        '--tokenizer_type',
        help=
        'Specify that argument when providing a .model file as the tokenizer_dir. '
        'It allows AutoTokenizer to instantiate the correct tokenizer type.')
    parser.add_argument('--vocab_file',
                        help="Used for sentencepiece tokenizers")
    parser.add_argument('--num_beams',
                        type=int,
                        help="Use beam search if num_beams >1",
                        default=1)
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--top_k', type=int, default=1)
    parser.add_argument('--top_p', type=float, default=0.0)
    parser.add_argument('--length_penalty', type=float, default=1.0)
    parser.add_argument('--repetition_penalty', type=float, default=1.0)
    parser.add_argument('--debug_mode',
                        default=False,
                        action='store_true',
                        help="Whether or not to turn on the debug mode")
    parser.add_argument('--no_add_special_tokens',
                        dest='add_special_tokens',
                        default=True,
                        action='store_false',
                        help="Whether or not to add special tokens")
    parser.add_argument('--streaming', default=False, action='store_true')
    parser.add_argument('--streaming_interval',
                        type=int,
                        help="How often to return tokens when streaming.",
                        default=5)
    parser.add_argument(
        '--prompt_table_path',
        type=str,
        help="Path to .npy file, exported by nemo_prompt_convert.py")
    parser.add_argument(
        '--prompt_tasks',
        help="Comma-separated list of tasks for prompt tuning, e.g., 0,3,1,0")
    parser.add_argument('--lora_dir',
                        type=str,
                        default=None,
                        help="The directory of LoRA weights")
    parser.add_argument(
        '--lora_task_uids',
        type=str,
        default=None,
        nargs="+",
        help="The list of LoRA task uids; use -1 to disable the LoRA module")
    parser.add_argument('--lora_ckpt_source',
                        type=str,
                        default="hf",
                        choices=["hf", "nemo"],
                        help="The source of lora checkpoint.")

    parser.add_argument(
        '--num_prepend_vtokens',
        nargs="+",
        type=int,
        help="Number of (default) virtual tokens to prepend to each sentence."
        " For example, '--num_prepend_vtokens=10' will prepend the tokens"
        " [vocab_size, vocab_size + 1, ..., vocab_size + 9] to the sentence.")

    return parser.parse_args(args=args)


def parse_input(tokenizer,
                input_text=None,
                prompt_template=None,
                input_file=None,
                add_special_tokens=True,
                max_input_length=923,
                pad_id=None,
                num_prepend_vtokens=[]):
    if pad_id is None:
        pad_id = tokenizer.pad_token_id

    batch_input_ids = []
    if input_file is None:
        for curr_text in input_text:
            if prompt_template is not None:
                curr_text = prompt_template.format(input_text=curr_text)
            input_ids = tokenizer.encode(curr_text,
                                         add_special_tokens=add_special_tokens,
                                         truncation=True,
                                         max_length=max_input_length)
            batch_input_ids.append(input_ids)
    else:
        if input_file.endswith('.csv'):
            with open(input_file, 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for line in csv_reader:
                    input_ids = np.array(line, dtype='int32')
                    batch_input_ids.append(input_ids[-max_input_length:])
        elif input_file.endswith('.npy'):
            inputs = np.load(input_file)
            for row in inputs:
                input_ids = row[row != pad_id]
                batch_input_ids.append(input_ids[-max_input_length:])
        elif input_file.endswith('.txt'):
            with open(input_file, 'r', encoding='utf-8',
                      errors='replace') as txt_file:
                input_text = txt_file.read()
                input_ids = tokenizer.encode(
                    input_text,
                    add_special_tokens=add_special_tokens,
                    truncation=True,
                    max_length=max_input_length)
                batch_input_ids.append(input_ids)
        else:
            print('Input file format not supported.')
            raise SystemExit

    if num_prepend_vtokens:
        assert len(num_prepend_vtokens) == len(batch_input_ids)
        base_vocab_size = tokenizer.vocab_size - len(
            tokenizer.special_tokens_map.get('additional_special_tokens', []))
        for i, length in enumerate(num_prepend_vtokens):
            batch_input_ids[i] = list(
                range(base_vocab_size,
                      base_vocab_size + length)) + batch_input_ids[i]

    batch_input_ids = [
        torch.tensor(x, dtype=torch.int32).unsqueeze(0) for x in batch_input_ids
    ]
    return batch_input_ids


def print_output(tokenizer,
                 output_ids,
                 input_lengths,
                 sequence_lengths,
                 context_logits=None,
                 generation_logits=None):
    batch_size, num_beams, _ = output_ids.size()
    for batch_idx in range(batch_size):
        inputs = output_ids[batch_idx][0][:input_lengths[batch_idx]].tolist(
        )
        #input_text = tokenizer.decode(inputs)
        #print(f'Input [Text {batch_idx}]: \"{input_text}\"')
        for beam in range(num_beams):
            output_begin = input_lengths[batch_idx]
            output_end = sequence_lengths[batch_idx][beam]
            outputs = output_ids[batch_idx][beam][
                output_begin:output_end].tolist()
            output_text = tokenizer.decode(outputs)
            print(
                f'Output [Text {batch_idx} Beam {beam}]: \"{output_text}\"')
            msg = json.dumps({'response': output_text}) + "\n"
            yield msg


runtime_rank = 0
tokenizer, pad_id, end_id = None, None, None
runner = None
# # An example to stop generation when the model generate " London" on first sentence, " eventually became" on second sentence
# stop_words_list = [[" London"], ["eventually became"]]
# stop_words_list = tensorrt_llm.runtime.to_word_list_format(stop_words_list, tokenizer)
# stop_words_list = torch.Tensor(stop_words_list).to(torch.int32).to("cuda").contiguous()
stop_words_list = None
# # An example to prevent generating " chef" on first sentence, " eventually" and " chef before" on second sentence
# bad_words_list = [[" chef"], [" eventually, chef before"]]
# bad_words_list = tensorrt_llm.runtime.to_word_list_format(bad_words_list, tokenizer)
# bad_words_list = torch.Tensor(bad_words_list).to(torch.int32).to("cuda").contiguous()
bad_words_list = None
model_name = None

def init(engine_dir, tokenizer_dir, vocab_file=None, tokenizer_type=None, lora_dir=None, lora_ckpt_source="hf", use_py_session=True, debug_mode=False, max_output_len=1000, num_beams=1, max_attention_window_size=None):
    global runtime_rank, tokenizer, pad_id, end_id, runner, stop_words_list, model_name
    runtime_rank = tensorrt_llm.mpi_rank()

    model_name = read_model_name(engine_dir)
    if tokenizer_dir is None:
        tokenizer_dir = DEFAULT_HF_MODEL_DIRS[model_name]

    tokenizer, pad_id, end_id = load_tokenizer(
        tokenizer_dir=tokenizer_dir,
        vocab_file=vocab_file,
        model_name=model_name,
        tokenizer_type=tokenizer_type,
    )


    if not PYTHON_BINDINGS and not use_py_session:
        logger.warning(
            "Python bindings of C++ session is unavailable, fallback to Python session."
        )
        use_py_session = True
    runner_cls = ModelRunner if use_py_session else ModelRunnerCpp
    runner_kwargs = dict(engine_dir=engine_dir,
                         lora_dir=lora_dir,
                         rank=runtime_rank,
                         debug_mode=debug_mode,
                         lora_ckpt_source=lora_ckpt_source)
    if not use_py_session:
        runner_kwargs.update(
            max_batch_size=1,
            max_input_len=4096,
            max_output_len=max_output_len,
            max_beam_width=num_beams,
            max_attention_window_size=max_attention_window_size)
    runner = runner_cls.from_dir(**runner_kwargs)
    
def inference(input_text, temperature=0.7, max_output_len= 512,
              top_k=1, top_p=0.0, length_penalty=1.0, repetition_penalty=1.0, 
              lora_task_uids=None,prompt_table_path="", prompt_tasks = [],
              streaming=False, streaming_interval = 1, use_prompt_template=False,
              add_special_tokens=True, max_input_length=923, num_prepend_vtokens=[], num_beams=1, max_attention_window_size=None):
    global runtime_rank, tokenizer, pad_id, end_id, runner, stop_words_list, model_name
    if tokenizer is None:
        init(engine_dir="/workspace/prj/trt_engines/mixtral/1gpu-int4", tokenizer_dir="/workspace/prj/Mixtral-8x7B-v0.1", max_output_len=512)
    if use_prompt_template and model_name in DEFAULT_PROMPT_TEMPLATES:
        prompt_template = DEFAULT_PROMPT_TEMPLATES[model_name]
    batch_input_ids = parse_input(tokenizer=tokenizer,
                                  input_text=input_text,
                                  prompt_template=None,
                                  input_file=None,
                                  add_special_tokens=add_special_tokens,
                                  max_input_length=max_input_length,
                                  pad_id=pad_id,
                                  num_prepend_vtokens=num_prepend_vtokens)
    input_lengths = [x.size(1) for x in batch_input_ids]

    t1 = time.time()
    with torch.no_grad():
        outputs = runner.generate(
            batch_input_ids,
            max_new_tokens=max_output_len,
            max_attention_window_size=max_attention_window_size,
            end_id=end_id,
            pad_id=pad_id,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            num_beams=num_beams,
            length_penalty=length_penalty,
            repetition_penalty=repetition_penalty,
            stop_words_list=stop_words_list,
            bad_words_list=bad_words_list,
            lora_uids=lora_task_uids,
            prompt_table_path=prompt_table_path,
            prompt_tasks=prompt_tasks,
            streaming=streaming,
            output_sequence_lengths=True,
            return_dict=True)
        torch.cuda.synchronize()
    t2 = time.time()
    print(f"time cost:{t2 - t1}, runk:{runtime_rank}")
    if runtime_rank == 0:
        if streaming:
            for curr_outputs in throttle_generator(outputs,
                                                   streaming_interval):
                output_ids = curr_outputs['output_ids']
                sequence_lengths = curr_outputs['sequence_lengths']
                
                batch_size, num_beams, _ = output_ids.size()
                for batch_idx in range(batch_size):
                    #inputs = output_ids[batch_idx][0][:input_lengths[batch_idx]].tolist()
                    #input_text = tokenizer.decode(inputs)
                    #print(f'Input [Text {batch_idx}]: \"{input_text}\"')
                    for beam in range(num_beams):
                        output_begin = input_lengths[batch_idx]
                        output_end = sequence_lengths[batch_idx][beam]
                        outputs = output_ids[batch_idx][beam][
                            output_begin:output_end].tolist()
                        output_text = tokenizer.decode(outputs)
                        print(
                            f'Output [Text {batch_idx} Beam {beam}]: \"{output_text}\"')
                        msg = json.dumps({'response': output_text}) + "\n"
                        yield msg
        else:
            output_ids = outputs['output_ids']
            sequence_lengths = outputs['sequence_lengths']
            context_logits = None
            generation_logits = None
            if runner.gather_all_token_logits:
                context_logits = outputs['context_logits']
                generation_logits = outputs['generation_logits']
            output_begin = input_lengths[0]
            output_end = sequence_lengths[0][0]
            outputs = output_ids[0][0][
                output_begin:output_end].tolist()
            output_text = tokenizer.decode(outputs)
            print(output_text)
            return output_text, []


if __name__ == "__main__":
    #args = parse_arguments(dict(engine_dir="/workspace/prj/trt_engines/mixtral/1gpu-int4", tokenizer_dir="/workspace/prj/Mixtral-8x7B-v0.1", max_output_len=1000, no_prompt_template=True))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)