from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

config = XttsConfig()
config.load_json("../XTTS-v2/config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="../XTTS-v2/", eval=True)
model.cuda()

def inference(text, speaker_wav, language):
  outputs = model.synthesize(
    text,
    config,
    speaker_wav=speaker_wav,
    gpt_cond_len=3,
    language=language,
  )
  wav = outputs['wav']
  return wav.tolist()

