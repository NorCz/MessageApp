import flask_login
from flask import Flask, request, make_response
from flask import jsonify
from hash import hash_password, check_password
from flask_login import login_user, LoginManager, logout_user, login_required
from db import db
from models import *




app = Flask(__name__)

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


#username, password, name, surname, email
@app.route('/api/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        data = request.json
        cipher_data = hash_password(data["password"])
        #trzeba dodać sprawdzanie czy użytkownik istnieje i dodać try catche
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


#username, password
@app.route('/api/login', methods=["POST"])
def login():
    #Trzeba dodać sprawdzenie czy użytkownik jest zalogowany
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


@app.route('/api/chats', methods=["GET"])
@login_required
def get_chats():
    result = db.session.query(GroupChat.id, GroupChat.name).select_from(GroupChat).join(ChatMember).filter(ChatMember.user_id == flask_login.current_user.id).all()
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

# POST /api/userlist/
# POST /api/user/{id} <- zwraca wiadomosci z danym użytkownikiem
# POST /api/user/{id}/send
# POST /api/chats/create
# POST /api/chats/{id}/add_user
# GET  /api/chats/ <- wyswietla czaty użytkownika
# GET  /api/chats/{id}/ <- wyswietla wiadomosci na czacie
# POST /api/chats/{id}/message/send



# GET  /api/user/settings
# POST /api/user/settings/set
