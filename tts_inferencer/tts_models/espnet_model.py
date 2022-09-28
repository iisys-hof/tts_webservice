
from typing import Dict
from tts_inferencer.tts_models.tts_model import TtsModel
from espnet2.bin.tts_inference import Text2Speech
from sklearn.preprocessing import StandardScaler
from parallel_wavegan.utils import read_hdf5
from parallel_wavegan.utils import load_model
import json
import torch

from tts_inferencer.utils.preprocessing import clean_input

class EspnetModel(TtsModel):
    def __init__(self, speaker_path, speaker_model, device = None) -> None:
        super().__init__(device)
        self.vocoder = None
        with open(f"{speaker_path}/{speaker_model.name}/inference_config.json", encoding="UTF-8") as cf:
                model_config = json.load(cf)
            
        if model_config["vocoder"]:
            vocoder_path = f"{speaker_path}/vocoder"
            self.vocoder = load_model(vocoder_path+"/checkpoint.pkl").to("cpu").eval()
            
            scaler = StandardScaler()
            scaler.mean_ = read_hdf5(vocoder_path+"/stats.h5", "mean")
            scaler.scale_ = read_hdf5(vocoder_path+"/stats.h5", "scale")
            scaler.n_features_in_ = scaler.mean_.shape[0]
            self.scaler = scaler
    
        model_path = f"{speaker_path}/{speaker_model.name}"
    
        self.model = Text2Speech(
        f"{model_path}/config.yaml", f"{model_path}/train.loss.best.pth",
        device=device,
        **model_config["mel_generator_config"]
        )
        self.model.spc2wav = None  # Disable griffin-lim
        #self.vocoder.remove_weight_norm()
        
        

    def inference(self, input_text, speaker_id=None):
        input_text = clean_input(input_text).sentence
        with torch.no_grad():
            output = self.model(input_text)
            wav = output["wav"]
            if self.vocoder is not None:
                d = output["feat_gen_denorm"]
                d = d.cpu()
                d = self.scaler.transform(d)
                wav = self.vocoder.inference(d)
                wav = torch.reshape(wav, (-1,))
            wav = wav.to("cpu").numpy()
        
        return wav
