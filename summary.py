import json
import requests
from settings import OLLAMA_API_URL

DEFAULT_PROMPT = "Write a concise summary of the text, return your responses with 5 lines that cover the key points of the text given."

def get_summary(text, systemPrompt):
  prompt = text
  if systemPrompt is None:
    systemPrompt = DEFAULT_PROMPT
  
  url = OLLAMA_API_URL

  payload = {
    "model": "llama2",
    "prompt": prompt, 
    "system": systemPrompt,
    "stream": False
  }
  payload_json = json.dumps(payload)
  headers = {"Content-Type": "application/json"}
  response = requests.post(url, data=payload_json, headers=headers)
  print(response.text)
  return json.loads(response.text)