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
from waitress import serve
import logging

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = "zse4%RDX"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)

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
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:3000"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With"
    return response


with app.app_context():
    db.create_all()


@app.route('/api', methods=["GET", "POST"])
def hello_world():
    return jsonify(
        response=True,
    )


@app.route('/api/userActive', methods=["POST"])
def user_active():
    u_id = current_user.get_id()
    User.query.filter_by(id=u_id).timestamp = datetime.datetime.now()
    db.session.commit()


@app.route('/api/getLoggedUsers', methods=["POST"])
def get_logged_users():
    users = User.query.all()
    list_of_active_users = []
    time = datetime.datetime.now()
    for u in users:
        if datetime.now() - u.lastRequest < datetime.timedelta(minutes=5):
            list_of_active_users.append(u.id)
    return json. dumps(list_of_active_users)


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


@app.route('/api/userlist', methods=["GET"])
@login_required
def userlist():
    list_of_users = User.query.all()
    json_of_users = {}
    for i in range(len(list_of_users)):
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

        if "content" not in params:
            return make_response(
                jsonify(
                    response=False
                ),
                400
            )

        with app.app_context():
            message = PrivateMessage(
                from_id=current_user.get_id(),
                to_id=user_id,
                content=params.get("content"),
            )
            if 'attachment' in params:
                message.attachment = params.get("attachment")
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


@app.route('/api/user/<user_id>/<page>', methods=["GET"])
@login_required
def private_messages(user_id, page):
    if User.query.get(user_id) and page.isdigit() and int(page) >= 0:
        u_id = current_user.get_id()
        messages = PrivateMessage.query.filter(
            PrivateMessage.from_id.in_((u_id, user_id)) & PrivateMessage.to_id.in_((u_id, user_id))).filter_by(
            isDeleted=False)
        list_of_messages_between_users = []
        for i in messages:
            if not i.isDeleted:
                list_of_messages_between_users.append(
                    {"message_id": i.id, "from": i.from_id, "to": i.to_id, "content": i.content,
                     "timestamp": i.timestamp, "attachment": i.attachment})
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
        code = RestoreCodes.query.filter_by(data["code"]).order_by(RestoreCodes.timestamp.desc()).filter_by(user_id=data["user"]).filter_by(confirmed=False).all()
        if len(code) == 0:
            return jsonify(
                response=False
            )
        else:
            #Bierzemy ostatni(zakładamy, że jest najwczesniejszy, czyli powinien być dobry)
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
        response += f"Successfully changed name to {user.name}. "
    if "surname" in data:
        user.surname = data["surname"]
        response += f"Successfully changed surname to {user.surname}. "
    if "email" in data:
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            response += "Email has been already taken."
        else:
            user.email = data["email"]
            response += f"Successfully changed email to {user.email}. "
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
    response = make_response(user.image, 404)
    response.mimetype = "text/plain"
    return response


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

    with app.app_context():
        chat = GroupChat(
            name=chat_name
        )

        db.session.add(chat)
        db.session.flush()
        db.session.refresh(chat)

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


@app.route('/api/chats/<chat_id>/<page>', methods=["GET"])
@login_required
def get_group_messages(chat_id, page):
    if GroupChat.query.get(chat_id) and page.isdigit() and int(page) >= 0:
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
    serve(app, listen='127.0.0.1:5000')

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
