# coding=utf-8
from application import bot
from boto3.session import Session
from model.song import Song
import requests
import os
import uuid
import spotipy


TOKEN = os.environ.get('BOT_TOKEN')
AUDD_API_TOKEN = os.environ.get('AUDD_API_TOKEN')

SPOTIFY_TOKEN = "BQAoGspigMn5fN_ZoTBfdSVkQSGm_pmFfSfbRmJqzCnoHJK1XFW24BAGAnWz-yM1ZDGHH_9S4cIj19tEcvo"
spotify = spotipy.Spotify(auth=SPOTIFY_TOKEN)

session = Session(aws_access_key_id=os.environ.get('AWS_S3_ACCESS_KEY'),
                  aws_secret_access_key=os.environ.get('AWS_S3_SECRET_KEY'))
s3 = session.resource('s3')
s3Client = session.client('s3')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


@bot.message_handler(func=lambda message: True, content_types=['voice'])
def echo_message(message):

    bot.reply_to(message, "⚙️ Procesando tu audio...", parse_mode="Markdown")

    fileId = message.voice.file_id
    getPathRequest = requests.get('https://api.telegram.org/bot' + TOKEN + '/getFile?file_id=' + fileId)
    if getPathRequest.status_code == 200:
        path = getPathRequest.json()['result']['file_path']
        rawFileRequest = requests.get('https://api.telegram.org/file/bot'+ TOKEN + '/' + path)
        if rawFileRequest.status_code == 200:
            fileKey = str(uuid.uuid4())

            upload = s3.Bucket('musictelegram').put_object(Key=fileKey, Body=rawFileRequest.content, ACL='public-read')

            bucket_location = s3Client.get_bucket_location(Bucket='musictelegram')
            object_url = "http://s3-{0}.amazonaws.com/{1}/{2}".format(
            bucket_location['LocationConstraint'],
            'musictelegram',
            fileKey)

            getSongInfo = requests.get('https://api.audd.io/?api_token=' + AUDD_API_TOKEN + '&url=' + object_url)
            if getSongInfo.status_code == 200:
                songInfo = getSongInfo.json()['result']
                songTitle = songInfo['title']
                songArtist = songInfo['artist']
                songAlbum = songInfo['album']

                messageToSend = ("Tu canción 🎶 es:\n"
                                "*Título:* {}\n"
                                "*Artista:* {}\n"
                                "*Album:* {}").format(songTitle.encode('utf-8'), songArtist.encode('utf-8'), songAlbum.encode('utf-8'))
                
                bot.send_message(message.chat.id, messageToSend, parse_mode="Markdown")
                
                spotifySearch = spotify.search(q='track:' + songTitle.encode('utf-8'), type='track')
                if(len(spotifySearch)):
                    spotifyURL = spotifySearch['tracks']['items'][0]['external_urls']['spotify']

                bot.send_message(message.chat.id, "*URL Spotify:* " + spotifyURL, parse_mode="Markdown")
                Song.set_config(message.chat.id, 'memory', songTitle, songAlbum, songArtist)
            else:
                bot.reply_to(message, "Error de reconocimiento de audio.")
        else:
            bot.reply_to(message, "Error procesando tu audio. Intentalo de nuevo.")
    else:
            bot.reply_to(message, "Error procesando tu audio. Intentalo de nuevo.")
