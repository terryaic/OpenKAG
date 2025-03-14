FROM nvcr.io/nvidia/pytorch:24.10-py3

COPY . /workspace/rag

WORKDIR /workspace/rag

RUN pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install third_parties/graphrag -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install open-text-embeddings[server] -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install openai-whisper soundfile httpx -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

RUN pip install openai-whisper soundfile httpx -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install langchain_community -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN apt update && apt install libcairo2 libcairo2-dev -y

COPY nltk_data /root/nltk_data
RUN pip install opencv-fixer && python -c "from opencv_fixer import AutoFix; AutoFix()"
RUN apt install libreoffice -y
