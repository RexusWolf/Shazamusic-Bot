# coding=utf-8
from datetime import datetime
from model import db

class Song(db.Model):
    __tablename__ = 'song'
    id = db.Column(db.Integer, primary_key=True)
    chat = db.Column(db.BigInteger, nullable=False)
    key = db.Column(db.String(255), nullable=False)
    title = db.Column(db.Text, nullable=False)
    album = db.Column(db.Text, nullable=False)
    artist = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def set_config(chat, key, title, album, artist):

        record = Song(chat=chat, key=key, title=title, album=album, artist=artist, created_at=datetime.now())
        db.session.add(record)

        db.session.commit()
        db.session.close()

        return record

    @staticmethod
    def get_config(chat, key):
        record = db.session.query(Song).filter_by(chat=chat, key=key).all()
        db.session.close()

        return record


