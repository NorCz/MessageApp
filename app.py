import flask_login
from flask import Flask, request, make_response, session
from flask import jsonify
from hash import hash_password, check_password, hash_password_with_salt_already_generated
from flask_login import login_user, LoginManager, logout_user, login_required, current_user
from flask_cors import CORS
from db import db
from models import *
import json

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = "zse4%RDX"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


with app.app_context():
    db.create_all()


@app.route('/api', methods=["GET", "POST"])
def hello_world():  # TODO: List api routes!
    return jsonify(
        response="API works correctly",
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
                response=f"Already logged in as user with id {current_user.id}"
            ),
            409
        )
    if request.data:
        data = request.json
        if "username" not in data or "password" not in data:
            return make_response(
                jsonify(
                    response="Request body missing username or password"
                ),
                400
            )
        user = User.query.filter_by(username=data["username"]).first_or_404()
        if check_password(data["password"], user.salt, user.password):
            login_user(user)
            session['user_id'] = current_user.id
            return jsonify(
                response="User successfully logged in!"
            )
        else:
            return make_response(
                jsonify(
                    response="Username or password does not match!"
                ),
                401
            )
    else:
        return make_response(
            jsonify(
                response="Request had an empty body"
            ),
            400
        )


@app.route('/api/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify(
        response="User successfully logged out!"
    )


#Userzy
@app.route('/api/userlist')
def userlist():
    list_of_users = User.query.all()
    json_of_users = {}
    for i in range(len(list_of_users)):
        json_of_users.update({f"User{i}": {"id": list_of_users[i].id, "username": list_of_users[i].username, "name": list_of_users[i].name, "surname": list_of_users[i].surname, "email": list_of_users[i].email}})
    return json.dumps(json_of_users)


@app.route('/api/started_conversations', methods=["GET"])
@login_required
def started_converstations():
    u_id = current_user.get_id()
    from_messages = PrivateMessage.query.filter((PrivateMessage.from_id == u_id) | (PrivateMessage.to_id == u_id)).distinct()
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


@app.route('/api/user/<user_id>/send', methods=["GET", "POST"])
@login_required
def send_message(user_id):
    if User.query.get_or_404(user_id):
        params = request.json
        with app.app_context():
            message = PrivateMessage(
                from_id=current_user.get_id(),
                to_id=user_id,
                content=params.get("content"),
                attachment=params.get("attachment")
            )
            db.session.add(message)
            db.session.commit()
        return jsonify(
            response="Message sent properly!"
        )


@app.route('/api/user/<user_id>', methods=["GET"])
@login_required
def private_messages(user_id):
    if User.query.get_or_404(user_id):
        u_id = current_user.get_id()
        messages = PrivateMessage.query.filter(PrivateMessage.from_id.in_((u_id, user_id)) & PrivateMessage.to_id.in_((u_id, user_id)))
        list_of_messages_between_users = []
        for i in messages:
            list_of_messages_between_users.append({"message_id": i.id, "from": i.from_id, "to": i.to_id, "content": i.content, "isDeleted": i.isDeleted, "timestamp": i.timestamp, "attachment": i.attachment})
        return json.dumps(list_of_messages_between_users, default=str)
    else:
        return jsonify(
            response="User not found in the database!"
        )


@app.route('/api/delete/<message_id>', methods=["DELETE"])
@login_required
def delete_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first_or_404()
    if message.from_id == current_user.get_id():
        message.isDeleted = True
        db.session.commit()
        return jsonify(
            response="Message successfully deleted!"
        )
    else:
        return jsonify(
            response="You are not allowed to delete this message!"
        )


@app.route('/api/change_password', methods=["PUT"])
def change_password():
    u_id = current_user.get_id()
    data = request.json
    user = User.query.filter_by(id=u_id).first()
    if "password" in data:
        user.password = hash_password_with_salt_already_generated(data["password"], user.salt)
        return jsonify(
            response="Password changed"
        )
    else:
        return make_response(
            jsonify(
                response="No password in request body!"
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


#Chaty
@app.route('/api/chats', methods=["GET"])
@login_required
def get_chats():
    result = db.session.query(GroupChat.id, GroupChat.name).select_from(GroupChat).join(ChatMember).filter(
        ChatMember.user_id == current_user.id).all()
    chats = []
    for row in result:
        members = db.session.query(ChatMember.id, ChatMember.user_id, ChatMember.nickname, ChatMember.isAdmin).filter_by(groupchat_id=row.id).all()
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


@app.route('/api/chats/create', methods=["PUT"])
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
    cur_member = db.session.query(ChatMember).filter_by(user_id=flask_login.current_user.id).join(GroupChat).filter_by(id=chat_id).first()
    if cur_member is None or not cur_member.isAdmin:
        return make_response(
            jsonify(
                response=f"Logged in user (id {flask_login.current_user.id}) is not a member of groupchat with id {chat_id} or not a groupchat admin"
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
            if db.session.query(ChatMember).filter_by(user_id=user_id).join(GroupChat).filter_by(id=chat_id).first() is not None:
                return make_response(
                    jsonify(
                        response=f"User with id {user_id} is already a member of groupchat with id {chat_id}."
                    ),
                    409
                )
            nickname = None
            if 'nickname' in data:
                nickname = data["nickname"]
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
# GET  /api/chats/{id}/ <- wyswietla wiadomosci na czacie
# POST /api/chats/{id}/message/send


# GET  /api/user/settings
# POST /api/user/settings/set
