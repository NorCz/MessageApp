import os
import sys
from datetime import datetime
import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from dotenv import load_dotenv
import subprocess


if not os.path.isfile('/app/backend/instance/project.db'):
    print('Database not yet created, AD service exiting.')
    exit()


class Base(DeclarativeBase):
    pass


# Model definitions
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, unique=False, nullable=False)
    salt = Column(String, unique=False, nullable=False)
    name = Column(String, unique=False, nullable=False)
    surname = Column(String, unique=False, nullable=False)
    email = Column(String, unique=True, nullable=False)
    image = Column(String, unique=False, nullable=True, default=None)
    lastRequest = Column(DateTime, unique=False, nullable=True, default=datetime.now)
    theme = Column(String, unique=False, nullable=False, default="standard")


class ChatMember(Base):
    __tablename__ = 'chatmember'

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    groupchat_id = Column(Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), unique=False, nullable=False)
    nickname = Column(String, unique=False, nullable=True, default=None)
    isAdmin = Column(Boolean, unique=False, nullable=False)
    isRemoved = Column(Boolean, unique=False, nullable=False, default=False)
    readTill = Column(String, unique=False, nullable=True, default=0)

    groupchat = relationship('GroupChat')
    user = relationship('User')


class GroupChat(Base):
    __tablename__ = 'groupchat'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, unique=False, nullable=False)


class GroupMessage(Base):
    __tablename__ = 'groupmessage'

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    member_id = Column(Integer, ForeignKey('chatmember.id'), unique=False, nullable=False)
    groupchat_id = Column(Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    content = Column(String, unique=False, nullable=False)
    isDeleted = Column(Boolean, unique=False, nullable=False, default=False)
    timestamp = Column(DateTime, unique=False, nullable=False, default=datetime.now)
    attachment = Column(LargeBinary, unique=False, nullable=True)

    member = relationship('ChatMember')
    groupchat = relationship('GroupChat')


class PrivateMessage(Base):
    __tablename__ = 'privatemessage'

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    from_id = Column(Integer, unique=False, nullable=False)
    to_id = Column(Integer, unique=False, nullable=False)
    content = Column(String, unique=False, nullable=True)
    isDeleted = Column(Boolean, unique=False, nullable=False, default=False)
    timestamp = Column(DateTime, unique=False, nullable=False, default=datetime.now)
    attachment = Column(String, unique=False, nullable=True)


class PrivateMessagesRead(Base):
    __tablename__ = 'privatemessagesread'
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    from_user_id = Column(Integer, unique=False, nullable=False)
    to_user_id = Column(Integer, unique=False, nullable=False)
    readTill = Column(String, unique=False, nullable=False)


class RestoreCodes(Base):
    __tablename__ = 'restorecodes'

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer, unique=False, nullable=False)
    code = Column(String, unique=False, nullable=False)
    timestamp = Column(DateTime, unique=False, nullable=False, default=datetime.now)
    confirmed = Column(Boolean, unique=False, nullable=False, default=False)


load_dotenv('/app/backend/.env', verbose=True, override=True)

server_dn_str = os.getenv("ad_server_dn")
split_arr = server_dn_str.split('.')
dn_arr = []
if len(split_arr) > 1:
    dn_arr = [dn for dn in split_arr if not dn.isspace()]
else:
    dn_arr = [server_dn_str]
group_cn = os.getenv("ad_group_cn")
username = os.getenv("ad_username")
password = os.getenv("ad_password")

engine = sqlalchemy.create_engine('sqlite:////app/backend/instance/project.db')
Session = sessionmaker(bind=engine)

print(f"[LDAP] Sending request to {' '.join(['ldapsearch', '-xLLL', '-H', f'ldap://{server_dn_str}', '-D', f'{username}@{server_dn_str}', '-w', password, '-b', ','.join([f'dc={dn}' for dn in dn_arr]), '-s', 'sub', f'cn={group_cn}', 'member'])}")
members_str = subprocess.check_output(['ldapsearch', '-xLLL', '-H', f'ldap://{server_dn_str}', '-D', f'{username}@{server_dn_str}', '-w', password, '-b', ','.join([f'dc={dn}' for dn in dn_arr]), '-s', 'sub', f'cn={group_cn}', 'member'])
print(members_str)
