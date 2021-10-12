import soundfile
from espnet2.bin.asr_inference import Speech2Text
import librosa
from pathlib import Path

package_path = Path(__file__).parent.absolute()

def inference_nemo_model(input_file, model_name):
    pass

def inference_huggingface_model(input_file, model_name):
    pass

def inference_esp_model(input_file, model_name):
    pass

def inference(input_file, model_name):
    model_path = str((package_path / f"models/{model_name}"))
    
    asr_train_config=model_path+"/asr_model/config.yaml"
    asr_model_file=model_path+"/asr_model/checkpoint.pth"
    lm_train_config=model_path+"/language_model/config.yaml"
    lm_file=model_path+"/language_model/checkpoint.pth"
    stt = Speech2Text(asr_train_config=asr_train_config,
                asr_model_file=asr_model_file,
                lm_train_config=lm_train_config,
                lm_file=lm_file,
                device="cpu",
                )

    audio, sr = librosa.load(input_file, sr=16000)
    

    stt_output = stt(audio)
    
    return stt_output[0][0]