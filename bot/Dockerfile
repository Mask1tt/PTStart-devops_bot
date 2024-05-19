FROM python:3.11-slim

WORKDIR /bot
COPY . /bot

COPY requirements.txt /bot
RUN pip install --upgrade pip 
RUN pip install --upgrade setuptools && pip install -r requirements.txt
RUN pip install python-telegram-bot==13.7
RUN pip install -U python-dotenv


CMD [ "python", "./bot.py" ]