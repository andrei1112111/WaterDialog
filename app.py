import os
from flask import Flask, redirect, url_for, request, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = '213 something'
app.config['SQLALCHEMY_DATABASE_URL'] = 'postgres://postgres:123@localhost/tea'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(16), nullable=False, unique=True)
    password = db.Column(db.String(16), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def hello_world():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    log = request.form.get('login')
    pas = request.form.get('password')
    if log and pas:
        user = User.query.filter_by(login=log).first()
        if user and check_password_hash(user.password, pas):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page:
                next_page = url_for('menu')
            return redirect(next_page)
        else:
            flash('Неверные логин/пароль')
    else:
        flash('Введите логин/пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    log = request.form.get('login')
    pas = request.form.get('password')
    pas2 = request.form.get('password2')
    if request.method == 'POST':
        if not (log or pas or pas2):
            flash('Заполните все поля')
        elif pas != pas2:
            flash('Пароли не равны')
        else:
            h_pas = generate_password_hash(pas)
            n_user = User(login=log, password=h_pas)
            db.session.add(n_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/menu')
@login_required
def menu():
    return 'qweqwe'


@app.after_request
def redirect_login(resp):
    if resp.status_code == 401:
        return redirect(f'{url_for("login")}?next={request.url}')
    return resp


@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
