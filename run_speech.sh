CUDA_VISIBLE_DEVICES=1 python backend/ttsapi.py &
CUDA_VISIBLE_DEVICES=2 python backend/asrapi.py &

cd backend
CUDA_VISIBLE_DEVICES=1 uvicorn asrapi:app  --reload --port 8089 --host 0.0.0.0 --ssl-keyfile ../data/certs/private.key --ssl-certfile ../data/certs/certificate.crt
