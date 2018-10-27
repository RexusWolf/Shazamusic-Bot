# coding=utf-8
from application import bot
from boto3.session import Session
from model.song import Song
import requests
import os
import uuid
import spotipy

humming_mode = False

TOKEN = os.environ.get('BOT_TOKEN')
AUDD_API_TOKEN = os.environ.get('AUDD_API_TOKEN')

SPOTIFY_API_TOKEN = os.environ.get('SPOTIFY_API_TOKEN')
spotify = spotipy.Spotify(auth=SPOTIFY_API_TOKEN)

session = Session(aws_access_key_id=os.environ.get('AWS_S3_ACCESS_KEY'),
                  aws_secret_access_key=os.environ.get('AWS_S3_SECRET_KEY'))
s3 = session.resource('s3')
s3Client = session.client('s3')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


@bot.message_handler(commands=['humming'])
def set_humming(message):
    global humming_mode
    humming_mode = True
    bot.reply_to(message, 'Se reconocerá como tarareo')


@bot.message_handler(commands=['recording'])
def set_recording(message):
    global humming_mode
    humming_mode = False
    bot.reply_to(message, 'Se reconocerá como grabación')

def get_song_info(title, artist, album, score = None):
    message = ""
    if title: message = message + "*Titulo:* " + title + "\n"
    if artist: message = message + "*Artista:* " + artist + "\n"
    if album: message = message + "*Album:* " + album + "\n"
    if score: message = message + "*Probabilidad:* " + str(score) + "\n"

    return message

@bot.message_handler(func=lambda message: True, content_types=['voice'])
def recognize_song(message):

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

            method = "recognizeWithOffset/" if humming_mode else ""

            getSongInfo = requests.get('https://api.audd.io/' + method +'?api_token=' + AUDD_API_TOKEN + '&url=' + object_url)
            if getSongInfo.status_code == 200:
                songInfo = getSongInfo.json()['result']
                if songInfo:
                    if humming_mode:
                        if songInfo['count']:
                            predictionList = songInfo['list']
                            bot.send_message(message.chat.id, "Tu canción puede ser una de estas:")
                            for prediction in predictionList:
                                title = None
                                artist = None
                                album = None
                                score = None
                                if prediction.has_key('title'): title = prediction['title']
                                if prediction.has_key('artist'): artist = prediction['artist']
                                if prediction.has_key('album'): album = prediction['album']
                                if prediction.has_key('score'): score = prediction['score']
                                bot.send_message(message.chat.id, get_song_info(title, artist, album, score), parse_mode="Markdown")
                        else:
                            bot.reply_to(message, "Lo has hecho fatal, intenta tararear de nuevo.")
                    else:
                        songTitle = songInfo['title']
                        songArtist = songInfo['artist']
                        songAlbum = songInfo['album']

                        messageToSend = "Tu cancion es:\n" + get_song_info(songTitle, songArtist, songAlbum)
                        
                        bot.send_message(message.chat.id, messageToSend, parse_mode="Markdown")
                        
                        spotifySearch = spotify.search(q='track:' + songTitle.encode('utf-8'), type='track')
                        if(len(spotifySearch)):
                            spotifyURL = spotifySearch['tracks']['items'][0]['external_urls']['spotify']

                        bot.send_message(message.chat.id, "*URL Spotify:* " + spotifyURL, parse_mode="Markdown")
                        Song.set_config(message.chat.id, 'memory', songTitle, songAlbum, songArtist)
                else:
                    bot.reply_to(message, "No se ha podido reconocer ninguna canción. Inténtalo de nuevo.")
            else:
                bot.reply_to(message, "Error de reconocimiento de audio.")
        else:
            bot.reply_to(message, "Error procesando tu audio. Intentalo de nuevo.")
    else:
            bot.reply_to(message, "Error procesando tu audio. Intentalo de nuevo.")
