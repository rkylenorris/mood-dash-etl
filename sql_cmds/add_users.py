import os
import bcrypt

from enum import Enum
from dotenv import load_dotenv
from sql_cmds import create_db_conn, execute_sql_command

load_dotenv()


class UserRole(Enum):
    ADMIN = 'admin'
    USER = 'user'
    PROVIDER = 'provider'


def add_user(username: str, name: str, password: str, role: UserRole, db_path: str = "data/daylio.db"):

    hashed_password = bcrypt.hashpw(password.encode(
        'utf-8'), bcrypt.gensalt()).decode('utf-8')

    sql_cmd = "INSERT INTO users (username, name, password_hash, role) VALUES (?, ?, ?, ?)"
    user_data = (username, name, hashed_password, role.value)

    execute_sql_command(create_db_conn(db_path), sql_cmd, True, user_data)

# TODO: Run script to add users, create login page, and set up authentication


def add_users():
    logins = [
        {
            "username": "admin",
            "name": "Kyle Norris",
            "password": os.getenv('ADMIN_PASSWORD', None),
            "role": UserRole.ADMIN
        },
        {
            "username": "therapist",
            "name": "Amanda Cosby",
            "password": os.getenv('PROVIDER_PASSWORD', None),
            "role": UserRole.PROVIDER
        }
    ]

    for login in logins:
        if login["password"] is None:
            raise ValueError(
                f"Password for user {login['username']} not set in environment variables.")
        add_user(
            username=login["username"],
            name=login["name"],
            password=login["password"],
            role=login["role"]
        )


if __name__ == "__main__":
    add_users()
