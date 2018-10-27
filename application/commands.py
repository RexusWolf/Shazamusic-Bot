# coding=utf-8
from application import bot
from boto3.session import Session
import requests
import os
import uuid

TOKEN = os.environ.get('BOT_TOKEN')
AUDD_API_TOKEN = os.environ.get('AUDD_API_TOKEN')

session = Session(aws_access_key_id=os.environ.get('AWS_S3_ACCESS_KEY'),
                  aws_secret_access_key=os.environ.get('AWS_S3_SECRET_KEY'))
s3 = session.resource('s3')
s3Client = session.client('s3')

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
    getPathRequest = requests.get('https://api.telegram.org/bot' + TOKEN + '/getFile?file_id=' + fileId)
    if getPathRequest.status_code == 200:
        path = getPathRequest['result']['file_path']
        rawFileRequest = requests.get('https://api.telegram.org/file/bot'+ TOKEN + '/' + path)
        if rawFileRequest.status_code == 200:
            fileKey = str(uuid.uuid4())

            upload = s3.Bucket('musictelegram').put_object(Key=fileKey, Body=rawFileRequest.content, ACL='public-read')

            bucket_location = s3Client.get_bucket_location(Bucket='musictelegram')
            object_url = "http://s3-{0}.amazonaws.com/{1}/{2}".format(
            bucket_location['LocationConstraint'],
            'musictelegram',
            fileKey)

            getSongInfo = requests.get('https://api.audd.io/?api_token=' + AUDD_API_TOKEN + '&url=' + object_url).json()
            if getSongInfo.status_code == 200:
                songInfo = getSongInfo['result']
                songTitle = songInfo['title']
                songArtist = songInfo['artist']
                songAlbum = songInfo['album']

                messageToSend = """
                *Título: * {}
                *Artista: * {}
                *Album: * {}
                    """.format(songTitle, songArtist, songAlbum)

                bot.reply_to(message, messageToSend, parse_mode="Markdown")
            else:
                bot.reply_to(message, "Error de reconocimiento de audio.")
        else:
            bot.reply_to(message, "Error procesando tu audio. Intentalo de nuevo.")
    else:
            bot.reply_to(message, "Error procesando tu audio. Intentalo de nuevo.")
