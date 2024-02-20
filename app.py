import json

import flask_login
from flask import Flask, request, make_response, session
from flask import jsonify
from hash import hash_password, check_password, hash_password_with_salt_already_generated
from flask_login import login_user, LoginManager, logout_user, login_required, current_user
from flask_cors import CORS
from db import db
from models import *
from datetime import timedelta

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
#app.config["SESSION_COOKIE_SECURE"] = True
app.secret_key = "9883f88db33793cae61c00a1a86a3e629f84c381687edbd62f83db96b9f36949"
app.permanent_session_lifetime = timedelta(days=3)

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


with app.app_context():
    db.create_all()


@app.route('/api', methods=["GET", "POST"])
def hello_world():
    return jsonify(
        response="true",
    )


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
                response="Request had an empty body"
            ),
            400
        )


# username, password
@app.route('/api/login', methods=["POST"])
def login():
    if current_user.is_authenticated:
        return make_response(
            jsonify(
                response=f"false"
            ),
            409
        )
    if request.data:
        data = request.json
        if "username" not in data or "password" not in data:
            return make_response(
                jsonify(
                    response="false"
                ),
                400
            )
        user = User.query.filter((User.username == data["username"]) | (User.email == data["username"])).first()
        if user is None:
            return make_response(
                jsonify(
                    response=f"User with username {data['username']} not found"
                ),
                404
            )
        if check_password(data["password"], user.salt, user.password):
            session.permanent = True
            login_user(user)
            return jsonify(
                response="true"
            )
        else:
            return make_response(
                jsonify(
                    response="false"
                ),
                401
            )
    else:
        return make_response(
            jsonify(
                response="false"
            ),
            400
        )


@app.route('/api/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify(
        response="true"
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


@app.route('/api/userlist')
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
                    response="false"
                ),
                400
            )
        params = request.json

        if "content" not in params:
            return make_response(
                jsonify(
                    response="false"
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
            response="true"
        )
    else:
        return make_response(
            jsonify(
                response=f"false"
            ),
            404
        )


@app.route('/api/user/<user_id>/<page>', methods=["GET"])
@login_required
def private_messages(user_id, page):
    if User.query.get(user_id):
        u_id = current_user.get_id()
        messages = PrivateMessage.query.filter(
            PrivateMessage.from_id.in_((u_id, user_id)) & PrivateMessage.to_id.in_((u_id, user_id))).filter_by(
            isDeleted=False)
        list_of_messages_between_users = []
        for i in messages:
            list_of_messages_between_users.append(
                {"message_id": i.id, "from": i.from_id, "to": i.to_id, "content": i.content, "isDeleted": i.isDeleted,
                 "timestamp": i.timestamp, "attachment": i.attachment})
        list_of_messages_between_users = list_of_messages_between_users[(int(page) - 1) * 30: int(page) * 30]
        return json.dumps(list_of_messages_between_users, default=str)
    else:
        return jsonify(
            response="false"
        )


@app.route('/api/delete/<message_id>', methods=["DELETE"])
@login_required
def delete_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first()
    if message is None:
        return make_response(
            jsonify(
                response=f"false"
            ),
            404
        )
    if message.from_id == current_user.get_id():
        message.isDeleted = True
        db.session.commit()
        return jsonify(
            response="true"
        )
    else:
        return make_response(
            jsonify(
                response="false"
            ),
            403
        )


@app.route('/api/recover_password', methods=["PUT"])
def recover_password():
    u_id = current_user.get_id()
    data = request.json
    user = User.query.filter((User.username == data["username"]) | (User.email == data["username"])).first()
    if "password" in data:
        user.password = hash_password_with_salt_already_generated(data["password"], user.salt)
        return jsonify(
            response="true"
        )
    else:
        return make_response(
            jsonify(
                response="false"
            ),
            400
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
    data = request.json
    u_id = current_user.get_id()
    if "image" in data:
        user = User.query.filter_by(id=u_id)
        user.image = data["image"]
        return jsonify(
            response="true"
        )
    else:
        return jsonify(
            response="false"
        )


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
            401
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
                    response="true"
                ),
                400
            )
        data = request.json
        cur_member = db.session.query(ChatMember).filter_by(user_id=flask_login.current_user.id).join(
            GroupChat).filter_by(id=chat_id).first()
        if cur_member is None:
            make_response(
                jsonify(
                    response=f"false"
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
            response="true"
        )
    else:
        return make_response(
            jsonify(
                response=f"false"
            ),
            404
        )


@app.route('/api/chats/<chat_id>/<page>', methods=["GET"])
@login_required
def get_group_messages(chat_id, page):
    if GroupChat.query.get(chat_id):
        cur_member = db.session.query(ChatMember).filter_by(user_id=flask_login.current_user.id).join(
            GroupChat).filter_by(id=chat_id).first()
        if cur_member is None:
            make_response(
                jsonify(
                    response=f"false"
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
                response=f"false"
            ),
            404
        )


if __name__ == '__main__':
    app.run(ssl_context='adhoc')

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
