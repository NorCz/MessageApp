import asyncio
import os
import secrets
import string
import sys
from datetime import datetime
import time
import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker, Session
from dotenv import load_dotenv
import subprocess
import base64
from hash import hash_password
from send_email import send_generic_email

avatar = ''
with open("/app/backend/default_avatar.txt") as f:
    avatar = f.read()

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
    image = Column(String, unique=False, nullable=True, default=avatar)
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
    readTill = Column(String, unique=False, nullable=True, default=time.time)

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

start_time = datetime.now()

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

print(f"[LDAP] Sending request to {' '.join(['ldapsearch', '-xLLL', '-H', f'ldap://{server_dn_str}', '-D', f'username@{server_dn_str}', '-w', 'password', '-b', ','.join([f'dc={dn}' for dn in dn_arr]), '-s', 'sub', f'cn={group_cn}', 'member'])}")
members_str = subprocess.check_output(['ldapsearch',
                                       '-xLLL',
                                       '-o', 'ldif-wrap=no',
                                       '-H', f'ldap://{server_dn_str}',
                                       '-D', f'{username}@{server_dn_str}',
                                       '-w', password,
                                       '-b', ','.join([f'dc={dn}' for dn in dn_arr]),
                                       '-s', 'sub',
                                       f'cn={group_cn}', 'member'])
decoded_members = []
chunking_detected = False
for line in members_str.decode('utf-8').split(os.linesep):
    if line.isspace() or line.strip().startswith('#'):
        continue
    if line.startswith('member:: '):
        line = line.replace('member:: ', '')
        line = base64.b64decode(str.encode(line)).decode('utf-8')
        cn = line.split(',')[0].replace('CN=', '')
        decoded_members.append(cn)
    if line.startswith('member;range=0-1499:: '):
        line = line.replace('member;range=0-1499:: ', '')
        line = base64.b64decode(str.encode(line)).decode('utf-8')
        cn = line.split(',')[0].replace('CN=', '')
        decoded_members.append(cn)
        chunking_detected = True
    elif line.startswith('member: '):
        line = line.replace('member: ', '')
        cn = line.split(',')[0].replace('CN=', '')
        decoded_members.append(cn)
    elif line.startswith('member;range=0-1499: '):
        line = line.replace('member;range=0-1499: ', '')
        cn = line.split(',')[0].replace('CN=', '')
        decoded_members.append(cn)
        chunking_detected = True

if chunking_detected:
    foundAsterisk = False
    startingChunk = 1500
    while not foundAsterisk:
        members_str = subprocess.check_output(['ldapsearch',
                                               '-xLLL',
                                               '-o', 'ldif-wrap=no',
                                               '-H', f'ldap://{server_dn_str}',
                                               '-D', f'{username}@{server_dn_str}',
                                               '-w', password,
                                               '-b', ','.join([f'dc={dn}' for dn in dn_arr]),
                                               '-s', 'sub',
                                               f'cn={group_cn}', f'member;range={startingChunk}-{startingChunk+1499}'])
        for line in members_str.decode('utf-8').split(os.linesep):
            if line.isspace() or line.strip().startswith('#'):
                continue
            if line.startswith(f'member;range={startingChunk}-{startingChunk+1499}:: '):
                line = line.replace(f'member;range={startingChunk}-{startingChunk+1499}:: ', '')
                line = base64.b64decode(str.encode(line)).decode('utf-8')
                cn = line.split(',')[0].replace('CN=', '')
                decoded_members.append(cn)
            if line.startswith(f'member;range={startingChunk}-*:: '):
                line = line.replace(f'member;range={startingChunk}-*:: ', '')
                line = base64.b64decode(str.encode(line)).decode('utf-8')
                cn = line.split(',')[0].replace('CN=', '')
                decoded_members.append(cn)
                foundAsterisk = True
            elif line.startswith(f'member;range={startingChunk}-{startingChunk+1499}: '):
                line = line.replace(f'member;range={startingChunk}-{startingChunk+1499}: ', '')
                cn = line.split(',')[0].replace('CN=', '')
                decoded_members.append(cn)
            elif line.startswith(f'member;range={startingChunk}-*: '):
                line = line.replace(f'member;range={startingChunk}-*: ', '')
                cn = line.split(',')[0].replace('CN=', '')
                decoded_members.append(cn)
                foundAsterisk = True
        startingChunk += 1500

imported_count = 0

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


groupi = 0
groups = list(chunks(decoded_members, 200))
for group in groups:
    querystring = f'(|{"".join([f"(cn={cn})" for cn in group if cn is not None])})'
    print(f"[LDAP] Sending request to {' '.join(['ldapsearch', '-xLLL', '-o', 'ldif-wrap=no', '-H', f'ldap://{server_dn_str}', '-D', f'username@{server_dn_str}', '-E', 'pr=500/noprompt', '-w', 'password', '-b', ','.join([f'dc={dn}' for dn in dn_arr]), '-s', 'sub', f'(|(cn=cn1)(cn=cn2)...)', 'givenName', 'sn', 'sAMAccountName', 'mail'])} (import request {groupi+1}/{len(groups)})")
    userinfo = subprocess.check_output(['ldapsearch',
                                        '-xLLL',
                                        '-o', 'ldif-wrap=no',
                                        '-H', f'ldap://{server_dn_str}',
                                        '-D', f'{username}@{server_dn_str}',
                                        '-E', 'pr=500/noprompt',
                                        '-w', password,
                                        '-b', ','.join([f'dc={dn}' for dn in dn_arr]),
                                        '-s', 'sub',
                                        querystring,
                                        'dn', 'givenName', 'sn', 'sAMAccountName', 'mail'])
    segments = userinfo.decode('utf-8').split(os.linesep + os.linesep)
    with Session(engine) as session:
        segment_counter = 0
        for segment in segments:
            segment_counter += 1
            user_dict = {}
            for line in segment.split(os.linesep):
                if line.isspace() or line.strip().startswith('#'):
                    continue
                if '::' in line:
                    split = line.split('::')
                    if split[0].strip() == 'dn':
                        user_dict['cn'] = base64.b64decode(str.encode(split[1].strip())).decode('utf-8').strip().split(',')[0].replace('CN=','')
                    else:
                        user_dict[split[0]] = base64.b64decode(str.encode(split[1].strip())).decode('utf-8')
                elif ':' in line:
                    split = line.split(':')
                    if split[0].strip() == 'dn':
                        user_dict['cn'] = split[1].strip().split(',')[0].replace('CN=','')
                    user_dict[split[0]] = split[1].strip()
            if 'cn' not in user_dict:
                continue
            if 'sn' not in user_dict:
                user_dict['sn'] = ''
            if 'givenName' not in user_dict:
                user_dict['givenName'] = ''
            if 'sAMAccountName' not in user_dict:
                print(f'[LDAP] User {user_dict["cn"]} missing username, not importing.')
                continue
            if 'mail' not in user_dict:
                print(f'[LDAP] User {user_dict["cn"]} missing mail, not importing.')
                continue
            if session.query(User).filter((User.username == user_dict['sAMAccountName']) | (User.email == user_dict['mail'])).first() is not None:
                # User already exists
                continue
            generated_password = ''.join([secrets.choice(string.ascii_letters + string.digits + '-_.#@!^&*') for _ in range(13)])
            cipher_data = hash_password(generated_password)
            user = User(
                username=user_dict['sAMAccountName'],
                password=cipher_data[0],
                salt=cipher_data[1],
                name=user_dict['givenName'],
                surname=user_dict['sn'],
                email=user_dict['mail']
            )
            session.add(user)
            imported_count += 1
            print(f"[LDAP] Imported user {user_dict['sAMAccountName']} ({segment_counter}/{len(segments)})")
            asyncio.run(send_generic_email(user_dict['mail'], "Subject: MessageApp - AD Account imported successfully", f"Hi there, your Active Directory account has been imported into the MessageApp communication system.\nYour generated password is {generated_password}, please change it upon login."))
        session.commit()
    groupi += 1

delta = datetime.now() - start_time

print(f"[LDAP] Imported {imported_count} users in {delta}, exiting.")
