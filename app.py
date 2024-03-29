import os
from flask import Flask, render_template, request, send_file, after_this_request
from flask_caching import Cache
import logging
from flask.globals import session
import tts_inferencer
import asr_inferencer
from pathlib import Path
import uuid
import json
from multiprocessing import Lock

app = Flask(__name__)

app.secret_key = uuid.uuid4().hex

app.config['CACHE_TYPE'] = 'simple'

all_models = []

models = None
##init models before app startup
with app.test_request_context():
    tts_models = tts_inferencer.get_models()
    for speaker, models in tts_models.items():
        for model in models.keys():
            if model != "vocoder" and model != "scaler":
                model_name = f"{speaker}_{model}"
                all_models.append(model_name)

models = tts_models

proc_lock = Lock()

logging.basicConfig(filename='record.log', level=logging.WARN, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

@app.before_request 
def before_request_callback():
    pass

@app.after_request 
def after_request_callback(response):
    session.pop("pending", None)
    return response

@app.route("/getmetadata", methods = ["GET"])
def get_metadata():
    wav_identifier = request.args["wav_identifier"].split(".")[0]
    metadata_file_path = f"temp/{wav_identifier}.txt"
    metadata = {}
    with open(metadata_file_path, encoding="UTF-8") as wav_metadata_file:
        metadata = json.load(wav_metadata_file)
    
    @after_this_request
    def remove_metadata_file(response):
        try:
            os.remove(metadata_file_path)
            return response
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
                
    return metadata

@app.route("/inferencetts", methods = ["POST"])
def inference_tts():
    if "pending" in session:
        return {"errormessage": "Only one request at a time is allowed" }, 401
    session["pending"] = 1
    inference_text = request.form["text_input"]
    model_id = request.form["model"]
    speaker_name,_,model_name = model_id.rpartition("_")
    if len(inference_text) > 300:
        try:
            session.pop("pending")
        except:
            pass
        return {"errormessage": "Inferencing ist auf maximal 300 Zeichen beschränkt." }, 500
    try:
        with proc_lock:
            wav = tts_inferencer.inference(inference_text, **models[speaker_name][model_name])
        @after_this_request
        def remove_wav_file(response):
            try:
                os.remove(wav)
                with open("./inferences.txt","a", encoding="UTF-8") as inferences_file:
                    inferences_file.write(inference_text+"\n")
                return response
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
        return send_file(wav,mimetype="audio/wav", as_attachment=True, download_name=str(wav)), 200
    except IOError as io_ex:
        app.logger.error(str(io_ex))
        return {"errormessage": f"Sprecherdaten für {model_id} noch nicht verfügbar. Bitte anderen Sprecher wählen."}, 500
    except RuntimeError as ru_ex:
        app.logger.error(str(ru_ex))
        return {"errormessage": "Kein oder fehlerhafter Text eingegeben."}, 500
    except Exception as ex:
        app.logger.error(str(ex))
        return {"errormessage": "Internal Server Error" }, 500

@app.route("/inferencestt", methods = ["POST"])
def inference_stt():
    if "pending" in session:
        return {"errormessage": "Only one request at a time is allowed" }, 401
    session["pending"] = 1
    inference_file = request.files["audio_1"]
    model_name = request.form["model_name"]
    try:
        inferenced_text = asr_inferencer.inference(inference_file, model_name)
        return {"inferenced_text":inferenced_text}, 200
    except IOError as io_ex:
        app.logger.error(str(io_ex))
        return {"errormessage":"Dieses Modell ist im Moment nicht verfügbar"}, 500
    except Exception as ex:
        app.logger.error(str(ex))
        return {"errormessage":str(ex)}, 500
    


@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html", models=all_models)

@app.route("/<place>")
def routeBasic(place):
    try:
        return render_template("{place}.html".format(place=place))
    except:
        return render_template("404.html".format(place=place))


if __name__ == '__main__':
    temp_path = Path("./temp")
    if not temp_path.exists():
        temp_path.mkdir()
    app.run(debug=True)
    