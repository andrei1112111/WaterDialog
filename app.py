import os.path
from flask import Flask, redirect, url_for, request, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_json import FlaskJSON, as_json
from sqlalchemy.exc import DatabaseError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from scripts import generate, train_classifier, parser

app = Flask(__name__)
FlaskJSON(app)
app.secret_key = '213 something'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('static/tea.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(16), nullable=False, unique=True)
    password = db.Column(db.String(16), nullable=False)
    datas = db.Column(db.String(255), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def hello_world():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
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
    elif log or pas:
        flash('Введите логин/пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    log = request.form.get('login')
    pas = request.form.get('password')
    pas2 = request.form.get('password2')
    if request.method == 'POST':
        if not (log or pas or pas2):
            flash('Заполните все поля')
        elif pas != pas2:
            flash('Пароли не равны')
        elif User.query.filter_by(login=log).first():
            flash('Недопустимый логин')
        else:
            h_pas = generate_password_hash(pas)
            n_user = User(login=log, password=h_pas)
            db.session.add(n_user)
            try:
                db.session.commit()
            except DatabaseError:
                db.session.rollback()
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    if request.method == 'POST':
        return redirect(f"http://127.0.0.1:5000/new/{request.form['selector']}")
    data = generate.generate(current_user.datas)
    return render_template('menu.html', table=data)


@app.route('/api/config/<name>')
@login_required
def config(name):
    if str(name.split('@')[-1]) != str(current_user.login):
        return 'У вас недостаточно прав!'
    data = db.session.query(User).filter(User.login == '1').scalar()
    return render_template('api_config.html', name=name)


@app.route('/new/<typi>', methods=['GET', 'POST'])
@login_required
def new_classify(typi):
    if typi == 'classify':
        pattern_data = {
            'type': 'classify',
            'files': ['carbon.png', 'carbon2.png', 'carbon6.png'],
            'img': 'left: -160px;'
        }
    elif typi == 'parser':
        pattern_data = {
            'type': 'parser',
            'files': ['carbon3.png', 'carbon4.png', 'carbon5.png'],
            'img': 'left: 80px;'
        }
    else:
        return redirect('http://127.0.0.1:5000/menu')
    if request.method == 'POST':
        f = request.form.to_dict()
        fi = request.files['file']
        if f['login'] and fi:
            if generate.correct_login(f['login']):
                if generate.correct_file(fi.filename):
                    if not current_user.datas or f'{f["login"]}@{pattern_data["type"]}@{current_user.login}|' not in current_user.datas:
                        path = f'user_data/{current_user.login}/{pattern_data["type"]}/{f["login"]}/data.json'
                        try:
                            os.mkdir(f'user_data/{current_user.login}')
                            os.mkdir(f'user_data/{current_user.login}/{pattern_data["type"]}')
                            os.mkdir(f'user_data/{current_user.login}/{pattern_data["type"]}/{f["login"]}')
                            print('ФАЙЛЫ ДАТЫ СОЗДАННЫ')
                        except FileExistsError as e:
                            print("ОШИБКА ПАПОК", e)
                        db.session.query(User)
                        a = db.session.query(User).filter(User.login == current_user.login)[0]
                        a.datas = str(a.datas) + f'{f["login"]}@{pattern_data["type"]}@{current_user.login}|'
                        try:
                            fi.save(path)
                        except FileExistsError as e:
                            print("ОШИБКА СОХРАНЕНИЯ", e)
                        try:
                            db.session.commit()
                        except DatabaseError:
                            print("ОШИБКА КОМИТА")
                            db.session.rollback()
                        return redirect(f'http://127.0.0.1:5000/api/config/{f["login"]}@{pattern_data["type"]}@{current_user.login}')
                    else:
                        return redirect(f'http://127.0.0.1:5000/api/config/{f["login"]}@{pattern_data["type"]}@{current_user.login}')
                else:
                    flash("Неверное заполнение файла данных")
            else:
                flash("Неверный формат логина(не больше 16 Английских букв)")
        else:
            flash("Введите имя api и загрузите .json")

    return render_template('new.html', data=pattern_data)


@app.route('/api/<key>', methods=['GET'])
@as_json
def api(key):
    response = None
    name, t, lo = key.split('@')
    path = f'user_data/{lo}/{t}/{name}'
    if generate.exists(path):
        data = request.args.get('data')
        if t == 'classify':
            response = train_classifier.ai_classify(data, path)
        elif t == 'parser':
            response = parser.parse_text_rules(data, path)
    if type(response) == dict:
        return response
    else:
        return dict(text=response)


@app.route('/error')
def error():
    code = request.args.get('code')
    if code == '404':
        text = 'Такой страницы не существует'
    else:
        text = 'Ошибка на сервере, извините :('
    return render_template('error.html', error_text=text, error=code)


@app.after_request
def redirect_login(resp):
    if resp.status_code == 401:
        return redirect(f'{url_for("login")}?next={request.url}')
    elif resp.status_code in [404, 500]:
        return redirect(f'{url_for("error")}?code={resp.status_code}')
    return resp


@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
