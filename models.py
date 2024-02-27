from flask_login import UserMixin
from sqlalchemy import ForeignKey
from db import db
from datetime import datetime
import time
avatar = ''
with open("default_avatar.txt") as f:
    avatar = f.read()


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)
    salt = db.Column(db.String, unique=False, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    surname = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    image = db.Column(db.String, unique=False, nullable=True, default=avatar)
    lastRequest = db.Column(db.DateTime, unique=False, nullable=True, default=datetime.now)
    theme = db.Column(db.String, unique=False, nullable=False, default="standard")


class ChatMember(db.Model):
    __tablename__ = 'chatmember'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    groupchat_id = db.Column(db.Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), unique=False, nullable=False)
    nickname = db.Column(db.String, unique=False, nullable=True, default=None)
    isAdmin = db.Column(db.Boolean, unique=False, nullable=False)
    isRemoved = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    readtill = db.Column(db.String, unique=False, nullable=True, default=time.time)

    groupchat = db.relationship('GroupChat')
    user = db.relationship('User')


class GroupChat(db.Model):
    __tablename__ = 'groupchat'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String, unique=False, nullable=False)


class GroupMessage(db.Model):
    __tablename__ = 'groupmessage'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    member_id = db.Column(db.Integer, ForeignKey('chatmember.id'), unique=False, nullable=False)
    groupchat_id = db.Column(db.Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)
    isDeleted = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    attachment = db.Column(db.String, unique=False, nullable=True)

    member = db.relationship('ChatMember')
    groupchat = db.relationship('GroupChat')


class PrivateMessage(db.Model):
    __tablename__ = 'privatemessage'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    from_id = db.Column(db.Integer, unique=False, nullable=False)
    to_id = db.Column(db.Integer, unique=False, nullable=False)
    content = db.Column(db.String, unique=False, nullable=True)
    isDeleted = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    attachment = db.Column(db.String, unique=False, nullable=True)


class PrivateMessagesRead(db.Model):
    __tablename__ = 'privatemessagesread'
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    from_user_id = db.Column(db.Integer, unique=False, nullable=False)
    to_user_id = db.Column(db.Integer, unique=False, nullable=False)
    readTill = db.Column(db.String, unique=False, nullable=False)


class RestoreCodes(db.Model):
    __tablename__ = 'restorecodes'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    code = db.Column(db.String, unique=False, nullable=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    confirmed = db.Column(db.Boolean, unique=False, nullable=False, default=False)


