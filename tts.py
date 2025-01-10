import requests
import json
from settings import TTS_URL, CHATTTS_URL

def tts_request(text, mode=None, locale=None):
    url = TTS_URL
    if mode == 'chat':
      url = CHATTTS_URL
    language = detect_lang(text)

    payload = {
        "content": text,
        "language": language,
        "locale": locale
    }

    try:
        # Send the POST request
        response = requests.post(url, data=payload)

        # Check the response
        if response.status_code == 200:
            output = response.content
            print(len(output))
            return True, output
        else:
            print(response.status_code)
    except Exception as e:
        print(e)
    return False, None
   
def detect_lang(text):
  from langdetect import detect
  try:
    detected_language = detect(text)
    return detected_language
  except Exception as e:
    pass
  return None
