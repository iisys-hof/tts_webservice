FROM python:3.8

WORKDIR /usr/src/app
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

CMD [ "/usr/local/bin/gunicorn", "-b", "0.0.0.0:80", "app:app" ]
