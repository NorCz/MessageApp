import bcrypt


def hash_password(p):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(p.encode('utf-8'), salt)
    return hashed_password, salt


def check_password(p, salt, hashed_password):
    return bcrypt.hashpw(p.encode('utf-8'), salt) == hashed_password
