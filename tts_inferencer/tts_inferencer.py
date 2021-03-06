from pathlib import Path
import torch
from espnet2.bin.tts_inference import Text2Speech
from parallel_wavegan.utils import load_model
import soundfile as sf
from sklearn.preprocessing import StandardScaler
from parallel_wavegan.utils import read_hdf5
import yaml
from pathlib import Path
from typing import List
import pandas as pd
from nltk.sem.evaluate import Error
from textblob import TextBlob
import re
import uuid
import json
import noisereduce as nr

package_path = Path(__file__).parent.absolute()
classHighlither = '###'
endOfClass = '____'

class ToString():
    def __str__(self):
        return ModelToStringConverter().convert(self) # pragma: no cover

class ModelToStringConverter:
    def convert(self, model):
        strings =[]
        strings.append( self.getClassText(model))
        strings.append('')
        attributes = self.getAllAttributes(model)
        [strings.append(self.getMethodText(model, attr)) for attr in attributes]
        strings.append(endOfClass)
        string = '\n'.join(strings)
        return string

    def getClassText(self,model):
        string = classHighlither + ' ' + model.__class__.__name__ + ' ' + classHighlither
        return string

    def getAllAttributes(self, model):
        attr:str
        allAttributes = dir(model)
        allAttributes = [attr for attr in allAttributes if not attr.startswith('__')]
        return allAttributes

    def getMethodText(self,model, methodName: str):
        value = getattr(model, methodName)
        valueString = self.getValueText(value)
        string = methodName + ' ' +  str(type(value)) +': ' + valueString
        return string
    
    def getValueText(self, value):
        if isinstance(value, float):
            return str(round(value,2))

        string = str(value)
        if len(string)>20:
            return string[:20] + ' ...'
        return str(value)

class PhoneticSentence(ToString):
    def __init__ (self, sentence: str, subWords: List[str]):
        self.sentence = sentence
        self.subWords = subWords

class Sentence(ToString):
    def __init__(self, sentence: str, id: str = ''):
        self.sentence = sentence
        self.id = id

    @property
    def words(self)-> List[str]:
        textBlob = TextBlob(self.sentence )
        wordList = list(textBlob.tokenize())
        return wordList

    @property
    def wordsCount(self):
        textBlob = TextBlob(self.sentence )
        wordCount = len(list(textBlob.words)) # type:ignore
        return wordCount

    @property
    def charCount(self):
        return len(self.sentence)


class SentenceToPhoneticSentenceConverter:
    def __init__(self, libraryPath: str ):
        self.library = self.createLibrary(libraryPath)


    def convert(self, sentence: Sentence):
        words = sentence.words
        ipaWords, subWords = self.transformSentencesToIpa(words)
        ipaText = ' '.join(ipaWords)
        return PhoneticSentence(ipaText, subWords)


    def createLibrary(self, libraryPath: str):
        pointLibrary = pd.DataFrame({
            "text": [",", ".", "?", "-", ";", "!", ":", "'", "s", "ste", "(", ")"],
            "ipa": [",", ".","?", ",", ",", "!", ":", "'", "s", "st??", ",", ","]
        })
        library = pd.read_csv(libraryPath,keep_default_na=False)

        libraryLowerCase = library.copy(deep=True)
        libraryLowerCase['text'] = libraryLowerCase['text'].apply(str.lower)
        library = library.append(pointLibrary)
        library = library.append(libraryLowerCase)

        library.set_index('text', inplace = True)
        library.sort_index(inplace = True)
        return library

    def transformSentencesToIpa(self, words:List[str]):
            ipaWords: List[str] = []
            subWords: List[str] = []
            index = 0
            while index < len(words):
                word = words[index]
                remainingWords = words[index:]
                countMultiwords, multiwords, multiWord = self.findMultiwordIpa(remainingWords)
                if countMultiwords>0 and multiwords is not None:
                    index += countMultiwords
                    subWords.append(multiWord)
                    ipaWords.append(multiwords)
                    continue
                ipa, subWord = self.transformWordToIpa(word)
                subWords.append(subWord)
                ipaWords.append(ipa)
                index +=1
            return ipaWords, subWords
    
    def findMultiwordIpa(self, words:List[str]):
        if len(words)<2:
            return 0, None, ""
        for count in range(5,1,-1):
            multiWord = ' '.join(words[:count])
            multiwordIpa = self.getIpaFromLibrary(multiWord)
            if multiwordIpa is not None:
                return count, multiwordIpa, multiWord
        return 0, None, ""

    def transformWordToIpa(self, word:str):
        completeIpaLeft = ''
        completeIpaRight = ''
        completeWordLeft = []
        completeWordRight = []
        while word != '':
            remainingWordFirst, ipaFirst, firstPart = self.findFirstPartInWord(word)
            remainingWordLast, ipaLast, lastPart = self.findLastPartInWord(word)
            if len(remainingWordLast) < len(remainingWordFirst):
                completeIpaLeft = ipaLast + completeIpaLeft
                completeWordLeft.insert(0,lastPart)
                word = remainingWordLast
            else:
                completeIpaRight = completeIpaRight + ipaFirst
                completeWordRight.append(firstPart)                
                word = remainingWordFirst
        completeIpa = completeIpaRight + completeIpaLeft
        completeWordRight.extend(completeWordLeft)
        completeWords = '|'.join(completeWordRight)
        return completeIpa, completeWords


    def findFirstPartInWord(self, word:str):
        for wordPart in range(len(word), 0, -1):
            part = word[:wordPart]
            ipa = self.getIpaFromLibrary(part)
            if ipa is not None:
                remainingWord = word[wordPart:]
                return remainingWord, ipa, part
        raise Error('we have no match for single char in library with char: ' + word[0])# pragma: no cover

    def findLastPartInWord(self, word:str):
        for wordPart in range(0,len(word)):
            part = word[wordPart:]
            ipa = self.getIpaFromLibrary(part)
            if ipa is not None:
                remainingWord = word[:wordPart]
                return remainingWord, ipa, part
        raise Error('we have no match for single char in library with char: ' + word[-1])# pragma: no cover

    def getIpaFromLibrary(self, word:str):
        ipa = self.getIpaFromLibraryExcactString(word)
        if ipa is  None:
            word = word.lower()
            ipa = self.getIpaFromLibraryExcactString(word)
        return ipa
    
    def getIpaFromLibraryExcactString(self,word:str):
        if word in self.library.index:
            ipa: str
            ipa = self.library.loc[word].values[0]
            if type(ipa) is not str:
                ipa = ipa[0]
            return ipa
        return None

converter = SentenceToPhoneticSentenceConverter(str((package_path / "phonemeLibraryGerman.csv")))

def inference(input_text, model, vocoder=None, scaler=None):
    model.spc2wav = None  # Disable griffin-lim
    #vocoder.remove_weight_norm()
    input_text = re.sub(r'[^\w\s\.,;?!????????]', " ", input_text)
    input_text = input_text.replace("???", "'")
    input_text = input_text.replace('[^\w\s\.,;?!????????]',' ')
    sentence = Sentence(input_text)
    phonetic_sentence = converter.convert(sentence)
    text = phonetic_sentence.sentence
    with torch.no_grad():
        output = model(text)
        wav = output["wav"]
        if vocoder is not None:
            d = output["feat_gen_denorm"]
            d = d.cpu()
            d = scaler.transform(d)
            wav = vocoder.inference(d)
            wav = torch.reshape(wav, (-1,))
        wav = wav.to("cpu").numpy()
        
        wav = nr.reduce_noise(y=wav, sr=22050, prop_decrease=0.5)
        
        identifier = str(uuid.uuid4())
        wav_id = "temp/"+ identifier
        wav_file_name = wav_id + ".wav"
        sf.write(wav_id + ".wav", wav, 22050, "PCM_16")
        with open(wav_id + ".txt", "w", encoding="UTF-8") as metadata_file:
            json.dump({"phonetic_sentence" : text, "subwords" : " ".join(phonetic_sentence.subWords)}, metadata_file)
        return wav_file_name
    
def get_models():
    tts_models = {}
    all_speakers = [p for p in Path("./tts_inferencer/speakers").iterdir() if p.is_dir() and p.name != "temp"]
    for speaker in all_speakers:
        speaker_name = speaker.name
        
        tts_models[speaker_name] = {}
        speaker_path = str(speaker.absolute())
        speaker_models = [model for model in speaker.iterdir() if model.is_dir() and model.name != "vocoder"]
        for speaker_model in speaker_models:
            tts_models[speaker_name][speaker_model.name] = {"vocoder" : None}
            with open(f"{speaker_path}/{speaker_model.name}/inference_config.json", encoding="UTF-8") as cf:
                model_config = json.load(cf)
            
            if model_config["vocoder"]:
                vocoder_path = f"{speaker_path}/vocoder"
                voc_config = None
                with open(vocoder_path+"/pre_config.yml") as f:
                        voc_config = yaml.load(f, Loader=yaml.Loader)
                vocoder = load_model(vocoder_path+"/checkpoint.pkl").to("cpu").eval()
                tts_models[speaker_name][speaker_model.name]["vocoder"] = vocoder
                
                scaler = StandardScaler()
                scaler.mean_ = read_hdf5(vocoder_path+"/stats.h5", "mean")
                scaler.scale_ = read_hdf5(vocoder_path+"/stats.h5", "scale")
                scaler.n_features_in_ = scaler.mean_.shape[0]
                tts_models[speaker_name][speaker_model.name]["scaler"] = scaler
        
            model_path = f"{speaker_path}/{speaker_model.name}"
        
            model = Text2Speech(
            f"{model_path}/config.yaml", f"{model_path}/train.loss.best.pth",
            device="cpu",
            **model_config["mel_generator_config"]
            )
            tts_models[speaker_name][speaker_model.name]["model"] = model
        
    return tts_models