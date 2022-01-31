from flask import Flask, redirect, url_for
from flask_login import LoginManager

app = Flask(__name__)

login_manager = LoginManager(app)

class User:


@app.route('/')
def hello_world():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return 'login'


if __name__ == '__main__':
    app.run()
