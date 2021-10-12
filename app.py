import os
from flask import Flask, render_template, request, send_file, after_this_request
import logging
from flask.globals import session
import tts_inferencer
import asr_inferencer
from pathlib import Path
import uuid

app = Flask(__name__)

app.secret_key = uuid.uuid4().hex

logging.basicConfig(filename='record.log', level=logging.WARN, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

@app.before_request 
def before_request_callback():
    pass

@app.after_request 
def after_request_callback(response):
    session.pop("pending", None)
    return response

@app.route("/inferencetts", methods = ["POST"])
def inference_tts():
    if "pending" in session:
        return {"errormessage": "Only one request at a time is allowed" }, 401
    session["pending"] = 1
    inference_text = request.form["text_input"]
    speaker_id = request.form["speaker"]
    if len(inference_text) > 300:
        try:
            session.pop("pending")
        except:
            pass
        return {"errormessage": "Inferencing ist auf maximal 300 Zeichen beschränkt." }, 500
    try:
        wav, phonemized_text = tts_inferencer.inference(inference_text, speaker_id)
        @after_this_request
        def remove_file(response):
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
        return {"errormessage": f"Sprecherdaten für {speaker_id} noch nicht verfügbar. Bitte anderen Sprecher wählen."}, 500
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
    return render_template("index.html")

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
    