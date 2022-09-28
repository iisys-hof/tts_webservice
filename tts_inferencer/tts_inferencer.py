from pathlib import Path
import torch
import soundfile as sf
from pathlib import Path
import uuid
import json
import noisereduce as nr

from tts_inferencer.tts_models.espnet_model import EspnetModel
from tts_inferencer.tts_models.fastpitch_hifigan import FastpitchHifigan
from tts_inferencer.tts_models.tts_model import TtsModel
from tts_inferencer.utils.preprocessing import clean_input




    

def inference(input_text, model:TtsModel, speaker_id:int, sr:int):
    wav = model.inference(input_text, speaker_id)
    
    input_sentence = clean_input(input_text)
    wav = nr.reduce_noise(y=wav, sr=sr, prop_decrease=0.5)
    identifier = str(uuid.uuid4())
    wav_id = "temp/"+ identifier
    wav_file_name = wav_id + ".wav"
    sf.write(wav_id + ".wav", wav, sr, "PCM_16")
    with open(wav_id + ".txt", "w", encoding="UTF-8") as metadata_file:
        json.dump({"phonetic_sentence" : input_sentence.sentence, "subwords" : " ".join(input_sentence.subWords)}, metadata_file)
    return wav_file_name
    

def get_models():
    device = "cpu"
    tts_models = {}
    all_speakers = [p for p in Path("./tts_inferencer/speakers").iterdir() if p.is_dir() and p.name != "temp"]
    for speaker in all_speakers:
        speaker_name = speaker.name
        
        tts_models[speaker_name] = {}
        speaker_path = str(speaker.absolute())
        speaker_models = [model for model in speaker.iterdir() if model.is_dir() and model.name != "vocoder"]
        for speaker_model in speaker_models:
            model = EspnetModel(speaker_path, speaker_model, device=device)
            tts_models[speaker_name][speaker_model.name] = {"model": model, "speaker_id" : None, "sr" : 22050}
    
    
    fastpitch_hifigan_speakers = FastpitchHifigan.speaker_ids
    fastpitch_hifigan_model = FastpitchHifigan(device=device)
    fastpitch_hifigan_name = "NVIDIA_Fastpitch_Hifigan"
    tts_models[fastpitch_hifigan_name] = {}
    for speaker in fastpitch_hifigan_speakers:
        tts_models[fastpitch_hifigan_name][f"Speaker{str(speaker)}"] = {"model" : fastpitch_hifigan_model, "speaker_id" : speaker, "sr" : 44100}
    return tts_models