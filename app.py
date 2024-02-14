import flask_login
from flask import Flask, request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from hash import hash_password, check_password
from flask_login import login_user, UserMixin, LoginManager, logout_user, login_required
from sqlalchemy import ForeignKey


app = Flask(__name__)

db = SQLAlchemy()

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = "zse4%RDX"
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


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
    nickname = db.Column(db.String, unique=False, nullable=False)
    isAdmin = db.Column(db.Boolean, unique=False, nullable=False)
    isRemoved = db.Column(db.Boolean, unique=False, nullable=False)

    groupchat = db.relationship('GroupChat')
    user = db.relationship('User')


class GroupChat(db.Model):
    __tablename__ = 'groupchat'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)


class GroupMessage(db.Model):
    __tablename__ = 'groupmessage'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    member_id = db.Column(db.Integer, ForeignKey('chatmember.id'), unique=False, nullable=False)
    groupchat_id = db.Column(db.Integer, ForeignKey('groupchat.id'), unique=False, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)
    isDeleted = db.Column(db.Boolean, unique=False, nullable=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False)
    attachment = db.Column(db.LargeBinary, unique=False, nullable=True)

    member = db.relationship('ChatMember')
    groupchat = db.relationship('GroupChat')


class PrivateChat(db.Model):
    __tablename__ = 'privatechat'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    from_id = db.Column(db.Integer, ForeignKey('user.id'), unique=False, nullable=False)
    to_id = db.Column(db.Integer, ForeignKey('user.id'), unique=False, nullable=False)

    from_user = db.relationship("User", foreign_keys=[from_id])
    to_user = db.relationship("User", foreign_keys=[to_id])


class PrivateMessage(db.Model):
    __tablename__ = 'privatemessage'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("user.id"), unique=False, nullable=False)
    privatechat_id = db.Column(db.Integer, ForeignKey('privatechat.id'), unique=False, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)
    isDeleted = db.Column(db.Boolean, unique=False, nullable=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False)
    attachment = db.Column(db.LargeBinary, unique=False, nullable=True)

    user = db.relationship("User")
    privateChat = db.relationship("PrivateChat")


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
            login_user(user)
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
            return jsonify(
                response="Username or password does not match!"
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
