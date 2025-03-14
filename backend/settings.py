#! -*- coding: utf-8 -*-

TTS_ENABLED = True
a2f_url = "localhost:50051"
samplerate = 22050
instance_name = "/World/LazyGraph/PlayerStreaming"
language = "en"
MAX_TOKENS = 2048
TEMPERATURE=0
OV_SRV_URL = "http://localhost:8011"

API_OPENAI = "OPENAI"
API_OLLAMA = "OLLAMA"
LLAMA_API_URL = "http://192.168.1.57:8088/api/generate"#"http://13902254981.tpddns.cn:8088/api/generate"#
VLLM_API_URL = "http://192.168.1.14:8085/v1/completions"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
TTS_URL = "http://192.168.1.57:9087/api/generate"

MODEL_NAME_ZEPHYR_LOCAL = '../openbuddy-zephyr-7b-v14.1'
MODEL_NAME_MIXTRAL_LOCAL = "mixtral-instruct-awq"#"../Mixtral-8x7B-v0.1"
MODEL_NAME_MISTRAL_LOCAL = "/media/lin/lib/models/Mistral-7B-Instruct-v0.2"
MODEL_NAME_MIXTRAL_LOCAL = "/media/lin/lib/models/Mixtral-8x7B-v0.1"
MODEL_NAME_MIXTRAL_OV_LOCAL = "/media/lin/lib/models/mixtral-8x7b-ov"

MODEL_NAME_ZEPHYR = "zephyr"
MODEL_NAME_LLMMA2 = "llama2"
MODEL_NAME_MIXTRAL = "mixtral-instruct-awq"#"mixtral"#"mixtral:8x7b-instruct-v0.1-q8_0"#
MODEL_NAME_MISTRAL = "Mistral-7B-Instruct-v0.2"

EN_STOP_WORDS = ['.',':']
CN_STOP_WORDS = ['。','：']
STOP_WORDS = ['。','：','.',':']


def get_llm_url():
    return VLLM_API_URL

def get_llm_model():
    return MODEL_NAME_MIXTRAL_LOCAL

def get_llm_model_local():
    return MODEL_NAME_MIXTRAL_OV_LOCAL

def streaming_mode():
    return True

def get_stop_words():
    return STOP_WORDS

def get_api_type():
    return API_OLLAMA

def get_peft_model():
    return MODEL_NAME_MIXTRAL_OV_LOCAL
WHISPERMODEL_SIZE="turbo"
WHISPERMODEL_SIZE_PATH="../models/whisper/large-v3-turbo.pt"
ALGIN_MODEL_PATH="example"

BATCHSIZE=16
# 加载 WhisperX 模型
DEVICE = "cuda"
DEVICCE_INDEX=0
COMPUTER_TYPE= "int8"

DIARIZATIONMODELPATH=None

DEFAULT_ASR_OPTIONS= {
    "beam_size": 5,
    "best_of": 5,
    "patience": 1,
    "length_penalty": 1,
    "repetition_penalty": 1,
    "no_repeat_ngram_size": 0,
    "temperatures": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    "compression_ratio_threshold": 2.4,
    "log_prob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": False,
    "prompt_reset_on_temperature": 0.5,
    "initial_prompt": "这是一段会议记录。",
    "prefix": None,
    "suppress_blank": True,
    "suppress_tokens": [-1],
    "without_timestamps": True,
    "max_initial_timestamp": 0.0,
    "word_timestamps": False,
    "prepend_punctuations": "\"'“¿([{-",
    "append_punctuations": "\"'.。,，!！?？:：”)]}、",
    "suppress_numerals": False,
    "max_new_tokens": None,
    "clip_timestamps": None,
    "hallucination_silence_threshold": None,
}

MODEL_DIARIZATION="/home/terry/models/"
ASR_PORT=8089


