from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import ForeignKey
from db import db

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)
    salt = db.Column(db.String, unique=False, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    surname = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)


class ChatMember(db.Model):
    __tablename__ = 'chatmember'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    groupchat_id = db.Column(db.Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), unique=False, nullable=False)
    nickname = db.Column(db.String, unique=False, nullable=True, default=None)
    isAdmin = db.Column(db.Boolean, unique=False, nullable=False)
    isRemoved = db.Column(db.Boolean, unique=False, nullable=False, default=False)

    groupchat = db.relationship('GroupChat')
    user = db.relationship('User')


class GroupChat(db.Model):
    __tablename__ = 'groupchat'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)


class PrivateChat(db.Model):
    __tablename__ = 'privatechat'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    from_id = db.Column(db.Integer, ForeignKey('user.id'), unique=False, nullable=False)
    to_id = db.Column(db.Integer, ForeignKey('user.id'), unique=False, nullable=False)

    from_user = db.relationship("User", foreign_keys=[from_id])
    to_user = db.relationship("User", foreign_keys=[to_id])


class GroupMessage(db.Model):
    __tablename__ = 'groupmessage'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    member_id = db.Column(db.Integer, ForeignKey('chatmember.id'), unique=False, nullable=False)
    groupchat_id = db.Column(db.Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)
    isDeleted = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    attachment = db.Column(db.LargeBinary, unique=False, nullable=True)

    member = db.relationship('ChatMember')
    groupchat = db.relationship('GroupChat')


class PrivateMessage(db.Model):
    __tablename__ = 'privatemessage'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("user.id"), unique=False, nullable=False)
    privatechat_id = db.Column(db.Integer, ForeignKey('privatechat.id'), unique=False, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)
    isDeleted = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.now)
    attachment = db.Column(db.LargeBinary, unique=False, nullable=True)

    user = db.relationship("User")
    privateChat = db.relationship("PrivateChat")
