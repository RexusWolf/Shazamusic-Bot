# coding=utf-8
from telebot import util
from application import bot
from model.song import Song


# @bot.message_handler(commands=['save'])
# def save(message):
#     """
#     Guarda un dato en el chat que se puede recuperar después
#     """

#     data = util.extract_arguments(message.text)
#     if not data:
#         bot.reply_to(message, "Debe indicar el dato que quiere que guarde")
#         return

#     chat_id = message.chat.id
#     Chat.set_config(chat_id, 'memory', data)
#     bot.reply_to(message, "Dato guardado. Usa /load para recuperar")


@bot.message_handler(commands=['load'])
def load(message):
    """
    Recupera un dato guardado con save
    """

    chat_id = message.chat.id
    data = Song.get_config(chat_id, 'memory')
    if not data:
        bot.reply_to(message, "Aún no has guardado nada")
        return

    songsMessage = ""

    for song in data:
        songTitle = song.title
        songArtist = song.artist
        songAlbum = song.album
        songInfo = "- " + songTitle + " | " + songArtist + " | " + songAlbum + "\n"
        songsMessage = songsMessage + songInfo.encode('utf-8') + "\n"

    messageToSend = "*Canciones que has buscado:*\n\n" + songsMessage
    bot.send_message(message.chat.id, messageToSend, parse_mode="markdown")
