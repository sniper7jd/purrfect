FROM python:3.11-slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN apt-get update && apt-get install -y bash


COPY app app
COPY migrations migrations
COPY purrfect.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP purrfect.py

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
