#!/bin/bash
pip install huggingface_hub --no-deps
export HF_ENDPOINT="https://hf-mirror.com"
# 定义多个模型名称
MODEL_NAMES=(
    "BAAI/bge-large-zh-v1.5"
    "BAAI/bge-reranker-base"
)

# 保存目录
SAVE_DIR="./models"

# 检查保存目录是否存在，不存在则创建
if [ ! -d "$SAVE_DIR" ]; then
  echo "目录 $SAVE_DIR 不存在，正在创建..."
  mkdir "$SAVE_DIR"
fi

WHISPER_URL="https://openaipublic.azureedge.net/main/whisper/models/aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a/large-v3-turbo.pt"
WHISPER_DIR="$SAVE_DIR/whisper"

# 检查 Whisper 模型目录是否存在，不存在则创建
if [ ! -d "$WHISPER_DIR" ]; then
  echo "Whisper 模型目录 $WHISPER_DIR 不存在，正在创建..."
  mkdir "$WHISPER_DIR"
fi

# 检查 Whisper 模型文件是否存在，存在则不下载
if [ ! -f "$WHISPER_DIR/large-v3-turbo.pt" ]; then
  echo "开始下载 Whisper 模型 $WHISPER_URL 到 $WHISPER_DIR ..."
  wget -c "$WHISPER_URL" -O "$WHISPER_DIR/large-v3-turbo.pt"
  echo "Whisper 模型下载完成！"
else
  echo "Whisper 模型已存在，跳过下载！"
fi

# 遍历每个模型名称并下载
for MODEL_NAME in "${MODEL_NAMES[@]}"; do
  # 创建模型对应的文件夹
  MODEL_DIR="$SAVE_DIR/$(basename "$MODEL_NAME")"

  # 检查模型目录是否存在，不存在则创建
  if [ ! -d "$MODEL_DIR" ]; then
    echo "目录 $MODEL_DIR 不存在，正在创建..."
    mkdir "$MODEL_DIR"
  fi

  # 检查模型文件是否已经下载，存在则跳过下载
echo "开始下载模型 $MODEL_NAME 到 $MODEL_DIR ..."
huggingface-cli download --resume-download "$MODEL_NAME" --local-dir "$MODEL_DIR"
echo "$MODEL_NAME 下载完成！"
done

# 保存目录
YOLO_SAVE_DIR="./models/YOLO"

# 使用 wget 直接下载
YOLO_URL="https://hf-mirror.com/opendatalab/PDF-Extract-Kit-1.0/resolve/main/models/Layout/YOLO/doclayout_yolo_ft.pt"

if [ ! -f "$YOLO_SAVE_DIR/doclayout_yolo_ft.pt" ]; then
  echo "开始下载 YOLO 模型到 $YOLO_SAVE_DIR ..."
  mkdir -p "$YOLO_SAVE_DIR"
  wget -c "$YOLO_URL" -O "$YOLO_SAVE_DIR/doclayout_yolo_ft.pt"
  echo "YOLO 模型下载完成！"
else
  echo "YOLO 模型已存在，跳过下载！"
fi

echo "所有模型下载完成！"
