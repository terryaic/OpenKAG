#! -*- coding: utf-8 -*-
language = "en"

TEMPERATURE=0

ASR_URL = 'http://localhost:8089/api/generate'

PROMPT_PREFIX = "使用中文回答："

API_OPENAI = "OPENAI"
def get_api_type():
    return API_OPENAI

D_URL='http://localhost/api/generate'

"""
avatar
"""
AVATAR_ENABLED = False
USING_ACE = True

"""
TTS
"""
TTS_ENABLED = True
USING_WAV_CACHE = True
CHATTTS_URL = "http://localhost/api/generate"
TTS_URL = "http://localhost/api/generate"



"""
stream输出的配置
"""
STOP_WORDS = ['。','.','！','？','\n']

def get_stop_words():
    return STOP_WORDS


"""
graphrag的配置
"""
DEFAULT_SETTINGS_PATH="./stores/default_setting"


"""
模型的配置
"""


# llm settings
VLLM_API_BASE_URL = "https://api.deepseek.com/beta"
MODEL_NAME = "deepseek-chat"
API_KEY="your-key"

def get_llm_base_url():
    return VLLM_API_BASE_URL

def get_llm_url():
    return VLLM_API_BASE_URL + "/generate"

# llm
MAX_TOKENS = 2048


def get_llm_model_local():
    return "" 

def get_peft_model():
    return ""

#llamaindex
USING_LLAMAINDEX = True
FILE_EXTS = ['.pdf','.doc','.txt', '.md','.xml','.docx','.pptx','.png','.jpg','.jpeg']
MAX_INPUT_TOKEN=32000
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
TOP_K=5

def get_llm_model():
    return MODEL_NAME

# graphrag的模型配置
GRAPHRAG_MODEL = "deepseek-chat"
GRAPHRAG_API_BASE_URL = "https://api.deepseek.com/beta"

GRAPHRAG_EMBEDDING_MODEL = "bge-large-zh-v1.5"
GRAPHRAG_EMBEDDING_API_BASE_URL = "http://localhost:8016/v1"
GRAPHRAG_EMBEDDING_API_KEY = "EMPTY"


#rag的模型配置
USING_RAG = False
RAG_LOCAL_EMBEDDING = False
EMBEDDING_DIM = 1024
USING_LANGCHAIN = False
RAG_USING_RERANK = False
RAG_RERANK_MODEL = "./models/bge-reranker-base"
RAG_EMBEDDING_MODEL = './models/bge-large-zh-v1.5'
RAG_RERANK_TOP_K = 8
TIMEOUT_RELEASE_INDEX = 600


"""
用户角色和权限
"""
IF_ANALYZE_ADDRESS = True
USER_PERMISSIONS = {
    "anonymous_user":[],
    "user":["rag","kdb","prompt","index","export"],
    "vip":["rag","multimodal","graphrag","uploadfile","kdb","prompt","index","export"],
    "admin":["rag", "multimodal", "graphrag", "share", "uploadfile", "kdb", "prompt", "index","export"] + \
            (["address"] if IF_ANALYZE_ADDRESS else [])
}

"""
多模态的配置
"""
#多模态的模型配置
MULTIMODAL_API_KEY = "EMPTY"
MULTIMODAL_BASE_URL = "http://localhost:8013/v1"
MULTIMODAL_MODEL_NAME = None
PDF_MODEL_PATH = "./models/YOLO/doclayout_yolo_ft.pt"

#允许的文件后缀
ALLOWEDEXTENSIONS = ['txt','md','xlsx','pptx','docx','doc','pdf',"mp3", "wav", "m4a", "flac", "aac", "ogg", "opus", "wma","ppt"]
MUlTIMODAL_ALLOWEDEXTENSIONS = ['jpg', 'jpeg', 'raw', 'png', "webp"]

# 多模态的清洗参数
PNG_SCALE = 2
PNG_DPI = 600
PNG_BACKGROUND_COLOR = "white"
IMAGE_MIN_SIZE = 100*50
IMAGE_MIN_WIDTH = 40
IMAGE_MIN_HEIGHT = 40

# 多模态的最大token
VLM_MAX_TOKEN=6144

MARKDOWN_URL = "http://localhost/api/generate"

"""
数据库的设置
"""

# 数据库类型
#DB_DEFAULT = "sqlite"
# sqlite的数据名字和地址
SQLITE_DB_PATH="data/chat.db"
SQL_DB_PATH_2USERS = "data/users.db"

# mongo的配置
DB_DEFAULT = "mongo"
DBNAME = "haifengllm" #mongo的数据库名字
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017


"""
邮箱配置
"""

# 邮箱设置
MAIL_USERNAME="example@xxxx.com"#显示的名字
MAIL_PASSWORD="xxxxxx"
MAIL_FROM="example@xxxx.com"#实际帐号
MAIL_PORT=465
MAIL_SERVER="xxxx.xxxxx.com"
MAIL_STARTTLS=False
MAIL_SSL_TLS=True
USE_CREDENTIALS=True


"""
是否查看logging
"""
DEBUG=False
PPT2PDF = False
DOC2PDF = False