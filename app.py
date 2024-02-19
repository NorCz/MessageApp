import flask_login
from flask import Flask, request, make_response
from flask import jsonify
from hash import hash_password, check_password
from flask_login import login_user, LoginManager, logout_user, login_required
from db import db
from models import *
import json

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = "zse4%RDX"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    global u_id
    u_id = user_id
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
    if request.method == "POST":
        data = request.json
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
        return jsonify(
            response="You cannot use GET to register!"
        )


# username, password
@app.route('/api/login', methods=["POST"])
def login():
    # Trzeba dodać sprawdzenie czy użytkownik jest zalogowany
    if request.method == "POST":
        data = request.json
        user = User.query.filter_by(username=data["username"]).first()
        if check_password(data["password"], user.salt, user.password):
            login_user(user)
            return jsonify(
                response="User successfully logged!"
            )
        else:
            return make_response(
                jsonify(
                    response="Username or password does not match!"
                ),
                401
            )
    else:
        return jsonify(
            response="You cannot use GET method to log!"
        )


@app.route('/api/logout', methods=["POST"])
@login_required
def logout():
    if request.method == "POST":
        logout_user()
        return jsonify(
            response="User successfully logged out!"
        )
    else:
        return jsonify(
            response="You cannot use GET method to logout!"
        )


#Userzy
@app.route('/api/userlist')
def userlist():
    list_of_users = User.query.all()
    json_of_users = {}
    for i in range(len(list_of_users)):
        json_of_users.update({f"User{i}": {"username": list_of_users[i].username, "name": list_of_users[i].name, "surname": list_of_users[i].surname, "email": list_of_users[i].email}})
    return json.dumps(json_of_users)


@app.route('/api/started_conversations', methods=["GET"])
@login_required
def started_converstations():
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
                from_id=u_id,
                to_id=user_id,
                content=params.get("content"),
                attachment=params.get("attachment")
            )
            db.session.add(message)
            db.session.commit()
        return jsonify(
            response="Message sent properly!"
        )
    else:
        return jsonify(
            response="User not found in the database"
        )


@app.route('/api/user/<user_id>', methods=["GET"])
@login_required
def private_messages(user_id):
    if User.query.get_or_404(user_id):
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
    message = PrivateMessage.query.filter_by(id=message_id).first()
    if message.from_id == u_id:
        message.isDeleted = True
        return jsonify(
            response="Message successfully deleted!"
        )
    else:
        return jsonify(
            response="You are not allowed to delete this message!"
        )


#Chaty
@app.route('/api/chats', methods=["GET"])
@login_required
def get_chats():
    result = db.session.query(GroupChat.id, GroupChat.name).select_from(GroupChat).join(ChatMember).filter(
        ChatMember.user_id == flask_login.current_user.id).all()
    chats = []
    for row in result:
        chats.append((row.id, row.name))
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
    db.session.flush()
    db.session.refresh(chat)

    member = ChatMember(
        user_id=flask_login.current_user.id,
        groupchat_id=chat.id,
        isAdmin=True,
        isRemoved=False,
        nickname=None
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


if __name__ == '__main__':
    app.run(ssl_context='adhoc')

# zrobione GET /api/
# zrobione POST /api/login
# zrobione POST /api/register
# zrobione GET /api/userlist/
# zrobione POST /api/user/{id} <- zwraca wiadomosci pomiędzy danymi użytkownikiem
# zrobione POST /api/user/{id}/send


# DELETE /api/message/{id}

# POST /api/chats/create
# POST /api/chats/{id}/add_user
# GET  /api/chats/ <- wyswietla czaty użytkownika
# GET  /api/chats/{id}/ <- wyswietla wiadomosci na czacie
# POST /api/chats/{id}/message/send


# GET  /api/user/settings
# POST /api/user/settings/set
