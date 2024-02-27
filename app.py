import os
import datetime
from datetime import timedelta
import json
from code_generator import generate_code
import flask_login
from flask import Flask, request, make_response, session
from flask import jsonify
from hash import hash_password, check_password, hash_password_with_salt_already_generated
from flask_login import login_user, LoginManager, logout_user, login_required, current_user
from flask_cors import CORS
from db import db
from models import *
from send_email import send_email
from dotenv import load_dotenv
import re
from sqlalchemy import or_
from sqlalchemy.sql import functions, expression

load_dotenv('.env', verbose=True, override=True)

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = os.getenv('secret_key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
app.config['SESSION_COOKIE_SECURE'] = True

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@login_manager.unauthorized_handler
def unauthorised():
    return make_response(
        jsonify(
            response="Unauthorized"
        ),
        401
    )


@app.after_request
def handle_options(response):
    response.headers["Access-Control-Allow-Origin"] = f"https://127.0.0.1:{os.getenv('server_port')}"
    response.headers["Access-Control-Allow-Credentials"] = "True"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With"
    if current_user is not None and current_user.is_authenticated:
        with app.app_context():
            db.session.get(User, current_user.id).lastUpdated = datetime.now()
            db.session.commit()
    return response


with app.app_context():
    db.create_all()


@app.route('/api', methods=["GET", "POST"])
def hello_world():
    return jsonify(
        response=True,
    )


@app.route('/api/userActive', methods=["POST"])
@login_required
def user_active():
    u_id = current_user.get_id()
    user = User.query.filter_by(id=u_id).first()
    user.lastRequest = datetime.now()
    db.session.commit()
    return jsonify(
        response=True
    )


@app.route('/api/getLoggedUsers', methods=["GET"])
def get_logged_users():
    users = User.query.all()
    list_of_active_users = []
    time = datetime.now()
    for u in users:
        print(f"{time}  {u.lastRequest}")
        if time - u.lastRequest < timedelta(minutes=5):
            list_of_active_users.append(u.id)
    return make_response(json.dumps(list_of_active_users), 200)


@app.route('/api/is_user_logged/<user_id>', methods=["GET"])
def is_user_logged(user_id):
    user = User.query.filter_by(id=user_id).first()
    if datetime.now() - user.lastRequest < timedelta(minutes=5):
        return make_response(jsonify(response=True), 200)
    else:
        return make_response(jsonify(response=False), 200)


# username, password, name, surname, email
@app.route('/api/register', methods=["POST"])
def register():
    if request.data:
        data = request.json
        if "username" not in data or "name" not in data or "surname" not in data or "email" not in data:
            return make_response(
                jsonify(
                    response="Request body missing at least one of: username, name, surname, email"
                ),
                400
            )
        if User.query.filter_by(username=data["username"]).first() is not None:
            return make_response(
                jsonify(
                    response="Username already exists"
                ),
                409
            )
        if User.query.filter_by(email=data["email"]).first() is not None:
            return make_response(
                jsonify(
                    response="Email already exists"
                ),
                409
            )
        if not re.match("^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$", data["email"]):
            return make_response(
                jsonify(
                    response="Invalid email address"
                ),
                400
            )
        if not len(data["password"]) >= 8:
            return make_response(
                jsonify(
                    response="Password too short"
                ),
                400
            )
        cipher_data = hash_password(data["password"])
        with app.app_context():
            user = User(
                username=data["username"],
                password=cipher_data[0],
                salt=cipher_data[1],
                name=data["name"],
                surname=data["surname"],
                email=data["email"]
            )
            db.session.add(user)
            db.session.commit()
        return jsonify(
            response="User succesfully added to database!"
        )
    else:
        return make_response(
            jsonify(
                response=False
            ),
            400
        )


# username, password
@app.route('/api/login', methods=["POST"])
def login():
    if current_user.is_authenticated:
        return make_response(
            jsonify(
                response=False
            ),
            409
        )
    if request.data:
        data = request.json
        if "username" not in data or "password" not in data:
            return make_response(
                jsonify(
                    response=False
                ),
                400
            )
        user = User.query.filter((User.username == data["username"]) | (User.email == data["username"])).first()
        if user is None:
            return make_response(
                jsonify(
                    response=False
                ),
                401
            )
        if check_password(data["password"], user.salt, user.password):
            login_user(user)
            session.permanent = True
            return jsonify(
                response=True
            )
        else:
            return make_response(
                jsonify(
                    response=False
                ),
                401
            )
    else:
        return make_response(
            jsonify(
                response=False
            ),
            400
        )


@app.route('/api/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify(
        response=True
    )


@app.route('/api/user', methods=["GET"])
@login_required
def get_current_user():
    return jsonify(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        surname=current_user.surname,
        email=current_user.email
    )


# Userzy
@app.route('/api/user/<user_id>', methods=["GET"])
@login_required
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return make_response(
            jsonify(
                response=f"User with id {user_id} not found"
            ),
            404
        )

    return jsonify(
        id=user.id,
        username=user.username,
        name=user.name,
        surname=user.surname,
        email=user.email
    )


@app.route('/api/get_image_of_user/<user_id>', methods=["GET"])
@login_required
def get_image_of_user(user_id):
    u = User.query.filter_by(id=user_id).first()
    return jsonify(
        id=u.id,
        image=u.image
    )


@app.route('/api/private_messages/read_till/<to_user>', methods=["GET", "POST"])
@login_required
def private_messages_read(to_user):
    u_id = int(current_user.get_id())
    if User.query.filter_by(id=to_user).first() is None:
        return make_response(
            jsonify(
                response=False
            ), 404
        )
    conv = PrivateMessagesRead.query.filter_by(from_user_id=u_id).filter_by(to_user_id=to_user).first()

    if request.method == "GET":
        if conv is not None:
            return make_response(
                jsonify(
                    logged_user=u_id,
                    to_id=conv.to_user_id,
                    read_till=int(conv.readTill)
                ), 200
            )
        else:
            return make_response(
                jsonify(
                    response=False
                ), 404
            )
    elif request.method == "POST":
        data = request.json
        if conv is not None:
            if "date" in data:
                with app.app_context():
                    converted_date = str(data["date"])
                    print('Conv found')
                    db.session.query(PrivateMessagesRead).filter_by(id=conv.id).update({'readTill': converted_date})
                    db.session.commit()
                    return make_response(
                        jsonify(
                            response=True
                        ), 200
                    )
            else:
                return make_response(
                    jsonify(
                        response=False
                    ),
                    400
                )
        else:
            with app.app_context():
                print('Conv not found')
                conv = PrivateMessagesRead(from_user_id=u_id, to_user_id=to_user, readTill=str(0))
                db.session.add(conv)
                db.session.commit()
            return make_response(
                jsonify(
                    response=True
                ), 200
            )


@app.route('/api/userlist', methods=["GET", "POST"], defaults={'page': 1})
@app.route('/api/userlist/<page>', methods=["GET", "POST"])
@login_required
def userlist(page):
    if (isinstance(page, str) and (not page.isdigit() or int(page) < 1)) or (isinstance(page, int) and page < 1):
        return make_response(
            jsonify(
                response=False
            ),
            400
        )
    search_str = ""
    if request.data:
        data = request.json
        if "search" in data:
            search_str = data["search"]
    t = []
    exclusion_list = []
    if request.data:
        data = request.json
        if "exc_list" in data:
            t = eval(json.dumps(data["exc_list"]))
            for i in t:
                if i.isdigit():
                    exclusion_list.append(int(i))
    list_of_users = User.query.filter(
        User.email.ilike(f"%{search_str}%") |
        User.username.ilike(f"%{search_str}%") |
        User.name.concat(" ").concat(User.surname).ilike(f"%{search_str}%")
    ).filter(User.id != current_user.id).paginate(page=int(page), per_page=30).items
    json_of_users = {}
    for i in range(len(list_of_users)):
        if list_of_users[i].id not in exclusion_list:
            json_of_users.update({f"User{i}": {"id": list_of_users[i].id, "username": list_of_users[i].username,
                                               "name": list_of_users[i].name, "surname": list_of_users[i].surname,
                                               "email": list_of_users[i].email}})
    return json.dumps(json_of_users)


@app.route('/api/started_conversations', methods=["GET"])
@login_required
def started_converstations():
    u_id = current_user.get_id()
    from_messages = PrivateMessage.query.filter(
        (PrivateMessage.from_id == u_id) | (PrivateMessage.to_id == u_id)).distinct()
    list_of_messages = []
    for i in from_messages:
        list_of_messages.append(i)
    list_of_messages.reverse()
    list_of_distinct_users = []
    for i in list_of_messages:
        if i.from_id != int(u_id) and i.from_id not in list_of_distinct_users:
            list_of_distinct_users.append(i.from_id)
        elif i.to_id != int(u_id) and i.to_id not in list_of_distinct_users:
            list_of_distinct_users.append(i.to_id)
    return jsonify(
        recentChats=list_of_distinct_users
    )


@app.route('/api/user/<user_id>/send', methods=["POST"])
@login_required
def send_message(user_id):
    if User.query.get(user_id):
        if not request.data:
            return make_response(
                jsonify(
                    response=False
                ),
                400
            )
        params = request.json
        u_id = current_user.get_id()
        if "content" not in params:
            return make_response(
                jsonify(
                    response=False
                ),
                400
            )

        with app.app_context():
            message = PrivateMessage(
                from_id=u_id,
                to_id=user_id,
                content=params.get("content"),
            )
            if 'attachment' in params:
                message.attachment = params.get("attachment")
            db.session.add(message)
            db.session.commit()
        u_id = current_user.get_id()
        m = PrivateMessagesRead.query.filter_by(from_user_id=u_id).filter_by(to_user_id=user_id).first()
        m.readTill = int(time.time() * 1000) + 1
        db.session.commit()
        return jsonify(
            response=True
        )
    else:
        return make_response(
            jsonify(
                response=False
            ),
            404
        )


@app.route('/api/user/<user_id>/<page>', methods=["GET"])
@login_required
def private_messages(user_id, page):
    if User.query.get(user_id) and page.isdigit() and int(page) >= 1:
        u_id = current_user.get_id()
        messages = PrivateMessage.query.filter(
            PrivateMessage.from_id.in_((u_id, user_id)) & PrivateMessage.to_id.in_((u_id, user_id))).filter_by(
            isDeleted=False)
        if page == 1:
            conv = PrivateMessagesRead.query.filter_by(from_user_id=u_id).filter_by(to_user_id=user_id).first()
            if conv is not None:
                conv.readTill = datetime.now()
                db.session.commit()
            else:
                conv = PrivateMessagesRead(from_user_id=u_id, to_user_id=user_id)
                db.session.add(conv)
        list_of_messages_between_users = []
        for i in messages:
            if not i.isDeleted:
                list_of_messages_between_users.append(
                    {"message_id": i.id, "from": i.from_id, "to": i.to_id, "content": i.content,
                     "timestamp": i.timestamp, "attachment": i.attachment})
        list_of_messages_between_users.reverse()
        list_of_messages_between_users = list_of_messages_between_users[(int(page) - 1) * 30: int(page) * 30]
        return json.dumps(list_of_messages_between_users, default=str)
    else:
        return make_response(
            jsonify(
                response=False
            ),
            400
        )


@app.route('/api/delete/<message_id>', methods=["DELETE"])
@login_required
def delete_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first()
    if message is None:
        return make_response(
            jsonify(
                response=False
            ),
            404
        )
    if message.from_id == current_user.get_id():
        message.isDeleted = True
        db.session.commit()
        return jsonify(
            response=True
        )
    else:
        return make_response(
            jsonify(
                response=False
            ),
            403
        )


@app.route('/api/send_email_with_recovery_code', methods=["POST"])
def recover_password():
    data = request.json
    if "username" in data:
        user = User.query.filter((User.username == data["username"]) | (User.email == data["username"])).first()
        with app.app_context():
            code = RestoreCodes(
                user_id=user.id,
                code=generate_code()
            )
            send_email(user.email, code)
            db.session.add(code)
            db.session.commit()
        return jsonify(
            response=True
        )
    else:
        return jsonify(
            response=False
        )


@app.route('/api/confirm_code', methods=["POST"])
def confirm_code():
    data = request.json
    if "code" in data and "user" in data:
        code = RestoreCodes.query.filter_by(data["code"]).order_by(RestoreCodes.timestamp.desc()).filter_by(
            user_id=data["user"]).filter_by(confirmed=False).all()
        if len(code) == 0:
            return jsonify(
                response=False
            )
        else:
            # Bierzemy ostatni(zakładamy, że jest najwczesniejszy, czyli powinien być dobry)
            code = code[len(code) - 1]
            code.confirmed = True
            db.session.commit()
            return jsonify(
                response=code.id
            )
    else:
        return jsonify(
            response=False
        )


@app.route('/api/reset_password', methods=["POST"])
def reset_password():
    data = request.json
    if "password" in data and "code" in data:
        code = RestoreCodes.query.filter_by(id=data["code"]).first()
        if datetime.now() - code.timestamp < datetime.timedelta(minutes=5):
            user = User.query.filter_by(id=code.user_id).first()
            user.password = hash_password_with_salt_already_generated(data["password"], user.salt)
            db.session.commit()
            return jsonify(
                response=True
            )
        else:
            return jsonify(
                response=False
            )
    return jsonify(
        response=False
    )


@app.route('/api/manage/', methods=["PUT"])
@login_required
def manage():
    u_id = current_user.get_id()
    data = request.json
    user = User.query.filter_by(id=u_id).first()
    response = ""
    if "name" in data:
        user.name = data["name"]
        response += f"Successfully changed name to {user.name}."
    if "surname" in data:
        user.surname = data["surname"]
        response += f"Successfully changed surname to {user.surname}."
    if "email" in data:
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            response += "Email has been already taken."
        else:
            user.email = data["email"]
            response += f"Successfully changed email to {user.email}."
    if "theme" in data:
        user.theme = data["theme"]
        response += f"Successfully changed theme to {user.theme}."
    db.session.commit()
    return jsonify(
        response=response
    )


@app.route('/api/change_image', methods=["POST"])
@login_required
def change_image():
    data = request.data.decode('utf-8')
    u_id = current_user.get_id()
    user = User.query.filter_by(id=u_id).first()
    user.image = data
    db.session.commit()
    return jsonify(
        response=True
    )


@app.route('/api/get_image', methods=["GET"])
@login_required
def get_image():
    u_id = current_user.get_id()
    user = User.query.filter_by(id=u_id).first()
    return make_response(
        jsonify(
            response="true",
            image=user.image
        ),
        200
    )


@app.route('/api/chats/change_chat_name', methods=["POST"])
@login_required
def change_chat_name():
    if request.json:
        data = request.json
        chat_id = data["id"]
        u_id = current_user.get_id()
        chat_member = ChatMember.query.filter_by(user_id=u_id).filter_by(groupchat_id=chat_id).first()
        if chat_member.isAdmin:
            chat = GroupChat.query.filter_by(id=chat_id).first()
            chat.name = data["name"]
        db.session.commit()
        return make_response(jsonify(response=True), 200)
    else:
        return make_response(jsonify(response=False), 409)


# Chaty
@app.route('/api/chats', methods=["GET"])
@login_required
def get_chats():
    result = db.session.query(GroupChat.id, GroupChat.name).select_from(GroupChat).join(ChatMember).filter(
        ChatMember.user_id == current_user.id).all()
    chats = []
    for row in result:
        members = db.session.query(ChatMember.id, ChatMember.user_id, ChatMember.nickname,
                                   ChatMember.isAdmin).filter_by(groupchat_id=row.id).all()
        chats.append(
            {
                "id": row.id,
                "name": row.name,
                "members": [{
                    "id": member.id,
                    "user_id": member.user_id,
                    "nickname": member.nickname,
                    "isAdmin": member.isAdmin
                } for member in members]
            }
        )
    return jsonify(
        chats=chats
    )


@app.route('/api/chats/create', methods=["POST"])
@login_required
def create_chat():
    chat_name = 'Nowa grupa'

    if request.data:
        data = request.json
        if 'name' in data:
            chat_name = data["name"]

    chat = GroupChat(
        name=chat_name
    )
    db.session.add(chat)
    db.session.commit()
    member = ChatMember(
        user_id=current_user.id,
        groupchat_id=chat.id,
        isAdmin=True
    )
    db.session.add(member)
    db.session.commit()

    return jsonify(
        {
            "response": f'Sucessfully created chat with id {chat.id} and name {chat.name}',
            "chat": {
                "id": chat.id,
                "name": chat.name
            }
        }
    )


@app.route('/api/chats/<chat_id>/add_user', methods=["POST"])
@login_required
def add_user_to_chat(chat_id):
    groupchat = db.session.query(GroupChat).filter_by(id=chat_id).first()
    if groupchat is None:
        return make_response(
            jsonify(
                response=f"Groupchat with id {chat_id} not found"
            ),
            404
        )
    cur_member = db.session.query(ChatMember).filter_by(user_id=flask_login.current_user.id).join(GroupChat).filter_by(
        id=chat_id).first()
    if cur_member is None:
        return make_response(
            jsonify(
                response=f"Groupchat with id {chat_id} not found"
            ),
            404
        )
    if not cur_member.isAdmin:
        return make_response(
            jsonify(
                response=f"User is not an admin in groupchat with id {chat_id}"
            ),
            403
        )

    if request.data:
        data = request.json
        if 'user_id' in data:
            user_id = data["user_id"]
            user = db.session.query(User).filter_by(id=user_id).first()
            if user is None:
                return make_response(
                    jsonify(
                        response=f"User with id {user_id} does not exist"
                    ),
                    404
                )
            if db.session.query(ChatMember).filter_by(user_id=user_id).join(GroupChat).filter_by(
                    id=chat_id).first() is not None:
                return make_response(
                    jsonify(
                        response=f"User with id {user_id} is already a member of groupchat with id {chat_id}."
                    ),
                    409
                )
            nickname = None
            if 'nickname' in data:
                nickname = data["nickname"]

            with app.app_context():
                member = ChatMember(
                    groupchat_id=chat_id,
                    user_id=user_id,
                    isAdmin=False,
                    nickname=nickname
                )

                db.session.add(member)
                db.session.commit()

            return jsonify(
                response='Successfully added user to chat',
            )
        else:
            return make_response(
                jsonify(
                    response="User's id was not provided in request body"
                ),
                400
            )
    else:
        return make_response(
            jsonify(
                response="Request had an empty body"
            ),
            400
        )


@app.route('/api/chats/<chat_id>/message/send', methods=["POST"])
@login_required
def send_group_message(chat_id):
    if GroupChat.query.get(chat_id):
        if not request.data:
            return make_response(
                jsonify(
                    response=True
                ),
                400
            )
        data = request.json
        cur_member = db.session.query(ChatMember).filter_by(user_id=flask_login.current_user.id).join(
            GroupChat).filter_by(id=chat_id).first()
        if cur_member is None:
            make_response(
                jsonify(
                    response=False
                )
            )

        with app.app_context():
            message = GroupMessage(
                member_id=cur_member.id,
                groupchat_id=chat_id,
                content=data["content"]
            )

            if 'attachment' in data:
                message.attachment = data.get("attachment")

            db.session.add(message)
            db.session.commit()
        return jsonify(
            response=True
        )
    else:
        return make_response(
            jsonify(
                response=False
            ),
            404
        )


@app.route('/api/chats/<chat_id>', methods=["GET"])
@login_required
def get_info_about_chat(chat_id):
    chat = GroupChat.query.filter_by(id=chat_id).first()
    return jsonify(
        id=chat.id,
        name=chat.name
    )


@app.route('/api/group_chats/read_till/<chat_id>', methods=["POST"])
@login_required
def gr_read_till(chat_id):
    if request.json:
        data = request.json
        if "date" in data:
            u_id = current_user.get_id()
            chat_member = ChatMember.query.filter_by(user_id=u_id).filter_by(groupchat_id=chat_id).first()
            chat_member.readtill = data["date"]
            db.session.commit()
            return make_response(jsonify(response=True), 200)
        else:
            return make_response(
                jsonify(
                    response=False
                ), 404
            )
    return make_response(
        jsonify(
            response=False
        ), 404
    )


@app.route('/api/chat/<chat_id>')
@login_required
def get_chat_member(chat_id):
    u_id = current_user.get_id()
    member = ChatMember.query.filter((ChatMember.groupchat_id == chat_id) & (ChatMember.user_id == u_id)).first()
    if member is not None:
        return jsonify(
            user_id=member.user_id,
            readtill=member.readtill
        )
    else:
        return make_response(jsonify(
            response=False
        ), 404)


@app.route("/api/chat/get_chat_member/<chat_id>/<user_id>", methods=["GET"])
def get_mem(chat_id, user_id):
    member = ChatMember.query.filter((ChatMember.groupchat_id == chat_id) & (ChatMember.user_id == user_id)).first()
    if member is not None:
        return jsonify(
            id=member.id,
            user_id=member.user_id,
            readtill=member.readtill,
            isAdmin=member.isAdmin,
            isRemove=member.isRemoved,
            groupchat_id=member.groupchat_id
        )
    else:
        return make_response(jsonify(
            response=False
        ), 404)


@app.route('/api/chats/<chat_id>/<page>', methods=["GET"])
@login_required
def get_group_messages(chat_id, page):
    if GroupChat.query.get(chat_id) and page.isdigit() and int(page) >= 1:
        cur_member = db.session.query(ChatMember).filter_by(user_id=flask_login.current_user.id).join(
            GroupChat).filter_by(id=chat_id).first()
        if cur_member is None:
            make_response(
                jsonify(
                    response=False
                )
            )

        messages = db.session.query(GroupMessage).filter_by(groupchat_id=chat_id).order_by(
            GroupMessage.timestamp.desc()).filter_by(isDeleted=False).all()
        if page == 1:
            u_id = current_user.get_id()
            user = ChatMember.query.filter_by(groupchat_id=chat_id).filter_by(user_id=u_id).first()
            user.readtill = datetime.now()
            db.session.commit()
        return jsonify(
            [{
                "id": message.id,
                "member_id": message.member_id,
                "groupchat_id": message.groupchat_id,
                "content": message.content,
                "timestamp": message.timestamp,
                "attachment": message.attachment
            } for message in messages][(int(page) - 1) * 30: int(page) * 30]
        )
    else:
        return make_response(
            jsonify(
                response=False
            ),
            404
        )


if __name__ == '__main__':
    app.run(ssl_context="adhoc")

# zrobione GET  /api/
# zrobione POST /api/login
# zrobione POST /api/register
# zrobione GET  /api/userlist/
# zrobione POST /api/user/{id} <- zwraca wiadomosci pomiędzy danymi użytkownikiem
# zrobione POST /api/user/{id}/send


# DELETE /api/message/{id}

# zrobione POST /api/chats/create
# zrobione POST /api/chats/{id}/add_user
# zrobione GET  /api/chats/ <- wyswietla czaty użytkownika
# zrobione GET  /api/chats/{id} <- wyswietla wiadomosci na czacie
# zrobione POST /api/chats/{id}/message/send


# GET  /api/user/settings
# POST /api/user/settings/set