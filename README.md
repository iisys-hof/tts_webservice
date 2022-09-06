#UPDATE SEMPTEMBER 2022
The phoneme dictionary was extended.
A VITS model trained on speaker data of "Hokuspokus Clean" was added.


# UPDATE JULY 2022
A VITS model trained on speaker data of "Bernd Ungerer" was added.

Text To Speech Inferencing Webservice based on Tacotron 2 and Multi-Band MelGAN, trained using the <a href="https://arxiv.org/abs/2106.06309">HUI-Audio-Corpus-German</a>, evaluated in <a href="https://www.thinkmind.org/index.php?view=article&articleid=centric_2021_2_30_30009">Neural Speech Synthesis in German</a>. Try it out at http://narvi.sysint.iisys.de/projects/tts.
Requirements:
- Linux-based OS (Ubuntu 18+, Debian9, Centos7)
- libfreetype6-dev
- pkg-configure
- Python >= 3.8
- python3-dev (for your respective version)
- libsndfile
- sox/ffmpeg

PyTorch may need to be installed separately (see https://pytorch.org/get-started/locally/)

Preparation:
Create virtual environment, install requirements
Open a python interpreter session in the previously generated virtual environment and run:
- import nltk
- nltk.download('punkt')

Before the TTS models can be used, download them from https://opendata.iisys.de/systemintegration/Models/speakers.tar.gz and extract them to tts_inferencer/speakers

Before the STT models can be used, download it from https://opendata.iisys.de/systemintegration/Models/asr_models.zip and extract them to asr_inferencer/models

To start the server in debug settings, run "python3 app.py". Access it at http://127.0.0.1:5000.

Further Notes:


If symbolic links for tacotron2 models are broken, recreate them using "ln -s <checkpoint.pth> train.loss.best.pth" in the respective speakers/<speaker>/tacotron2 directories.

Keep in mind, this service does not include number normalization yet, so do not input any digits (2 -> zwei).

The incorporated ASR model was taken from https://github.com/AASHISHAG/deepspeech-german, check out their work: https://www.researchgate.net/publication/336532830_German_End-to-end_Speech_Recognition_based_on_DeepSpeech.