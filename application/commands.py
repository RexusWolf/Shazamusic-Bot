# coding=utf-8
from application import bot
from boto3.session import Session
import requests
import os

TOKEN = os.environ.get('BOT_TOKEN')

session = Session(aws_access_key_id=os.environ.get('AWS_S3_ACCESS_KEY'),
                  aws_secret_access_key=os.environ.get('AWS_S3_SECRET_KEY'))
s3 = session.resource('s3')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


@bot.message_handler(func=lambda message: True, content_types=['voice'])
def echo_message(message):
    """
    Hace un 'eco' de lo que se recibe y no se ha procesado en algún comando anterior.
    :param message:
    :return:
    """
    fileId = message.voice.file_id
    getPathRequest = requests.get('https://api.telegram.org/bot' + TOKEN + '/getFile?file_id=' + fileId).json()
    path = getPathRequest['result']['file_path']
    rawFileRequest = requests.get('https://api.telegram.org/file/bot'+ TOKEN + '/' + path)

    
    s3.Bucket('musictelegram').put_object(Key='file.oga', Body=rawFileRequest.content)
    bot.reply_to(message, "HOLA")
