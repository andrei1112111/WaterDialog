import os.path
from flask import Flask, redirect, url_for, request, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse
from sqlalchemy.exc import DatabaseError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.datastructures import FileStorage
from scripts import generate, train_classifier, parser

app = Flask(__name__)
api = Api(app)
app.secret_key = '213 something'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('static/tea.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)
login_manager = LoginManager(app)


def go_api(data, text):
    if generate.exists(data.data_file):
        if data.type == 'classify':
            response = train_classifier.ai_classify(text, data.data_file)
        else:
            response = parser.parse_text_rules(text, data.data_file)
        data.views += 1
        try:
            db.session.merge(data)
            db.session.flush()
            db.session.commit()
        except DatabaseError:
            print("ОШИБКА КОМИТА")
            db.session.rollback()
        return False, response
    else:
        return True, 'Файл данных поврежден'


def create_file(args, file):
    path = f'user_data/{args.login}/{args.type}/{args.name}/data.json'
    try:
        os.mkdir(f'user_data/{args.login}')
    except FileExistsError:
        pass
    try:
        os.mkdir(f'user_data/{args.login}/{args.type}')
    except FileExistsError:
        pass
    try:
        os.mkdir(f'user_data/{args.login}/{args.type}/{args.name}')
    except FileExistsError:
        pass
    try:
        file.save(path)
    except FileExistsError as e:
        print("ОШИБКА СОХРАНЕНИЯ", e)
        return "ОШИБКА СОХРАНЕНИЯ", path
    return None, path


class WaterDialog(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):  # Запрос на выполнение прогрессинга текста
        result = {}
        pars = reqparse.RequestParser()
        pars.add_argument('id', type=int, required=True)
        pars.add_argument('text', type=str, required=True)
        pars.add_argument('login', type=str, required=False)
        pars.add_argument('password', type=str, required=False)
        args = pars.parse_args()
        data = db.session.query(Classifier).filter(Classifier.id == args.id).scalar()
        if args.id and data:
            if args.text:
                if data.for_all:
                    bad, res = go_api(data, args.text)
                    if bad:
                        result['error'] = "Файл данных поврежден или отсутствует"
                    else:
                        result['response'] = res
                else:
                    if args.login and args.password:
                        user = User.query.filter_by(login=args.login).first()
                        if user and check_password_hash(user.password, args.password):
                            result['auth'] = True
                            if user.login in data.admin_users or user.login in data.api_users or data.for_all is True:
                                bad, res = go_api(data, args.text)
                                if bad:
                                    result['error'] = "Файл данных поврежден или отсутствует"
                                else:
                                    result['response'] = res
                            else:
                                result['error'] = 'В доступе отказано'
                        else:
                            result['error'] = 'Неверная комбинация логина/пароля'
                    else:
                        result['error'] = 'Неверная комбинация логина/пароля'
            else:
                result['error'] = 'Текст запроса не указан'
        else:
            result['error'] = 'Не верный ключ api'
        return result


class WaterDialogSettings(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):  # Запрос на получение данных api
        result = {}
        pars = reqparse.RequestParser()
        pars.add_argument('id', type=int, required=True)
        pars.add_argument('login', type=str, required=True)
        pars.add_argument('password', type=str, required=True)
        args = pars.parse_args()
        data = db.session.query(Classifier).filter(Classifier.id == args.id).scalar()
        if args.id and data:
            if args.login and args.password:
                user = User.query.filter_by(login=args.login).first()
                if user and check_password_hash(user.password, args.password):
                    result['auth'] = True
                    if user.login in data.admin_users:
                        result['response'] = {
                            'key': data.id,
                            'name': data.name,
                            'admin_users': data.admin_users,
                            'api_users': data.api_users,
                            'for_all': data.for_all,
                            'views': data.views,
                            'type': data.type
                        }
                    else:
                        result['error'] = 'В доступе отказано'
                else:
                    result['error'] = 'Неверная комбинация логина/пароля'
            else:
                result['error'] = 'Неверная комбинация логина/пароля'
        else:
            result['error'] = 'Не верный ключ api'
        return result

    # noinspection PyMethodMayBeStatic
    def post(self):  # Запрос на создание нового api
        result = {}
        pars = reqparse.RequestParser()
        pars.add_argument('login', type=str, required=True)
        pars.add_argument('password', type=str, required=True)
        pars.add_argument('name', type=str, required=True)
        pars.add_argument('admin_users', type=str, required=False, action='append')
        pars.add_argument('api_users', type=list, required=False, action='append')
        pars.add_argument('type', type=str, required=True)
        pars.add_argument('for_all', type=str, required=False)
        pars.add_argument('data_file', type=FileStorage, location='files', required=True)
        args = pars.parse_args()
        admins = [args.login]
        if args.admin_users:
            admins.append(args.admin_users)
        if args.login and args.password:
            user = User.query.filter_by(login=args.login).first()
            if user and check_password_hash(user.password, args.password):
                result['auth'] = True
                if generate.correct_login(args.name):
                    file = args['data_file']
                    s = 'cl' if args.type == 'classify' else 'pa'
                    if generate.correct_file(file.filename, rule=s):
                        e, path = create_file(args, file)
                        if e:
                            result['response'] = e
                        new_classifier = Classifier(
                            name=args.name,
                            admin_users=admins,
                            api_users=args.api_users,
                            type=args.type,
                            for_all=False if args.for_all == 'False' else True,
                            data_file=path)
                        try:
                            db.session.add(new_classifier)
                            db.session.commit()
                            result['response'] = 'Успешно'
                        except DatabaseError:
                            print("ОШИБКА КОМИТА")
                            db.session.rollback()
                            result['response'] = 'Ошибка создания'
                        if user.classifiers != '':
                            user.classifiers = f'{user.classifiers}@{new_classifier.id}'
                        else:
                            user.classifiers = str(new_classifier.id)
                        try:
                            db.session.merge(user)
                            db.session.flush()
                            db.session.commit()
                        except DatabaseError:
                            print("ОШИБКА КОМИТА")
                            db.session.rollback()
                    else:
                        result['error'] = "Неверное заполнение файла данных"
                else:
                    result['error'] = "Неверный формат логина(не больше 16 Английских букв)"
            else:
                result['error'] = 'Неверная комбинация логина/пароля'
        else:
            result['error'] = 'Неверная комбинация логина/пароля'

        return result

    # noinspection PyMethodMayBeStatic
    def put(self):  # Запрос на изменение api
        result = {}
        pars = reqparse.RequestParser()
        pars.add_argument('login', type=str, required=True)
        pars.add_argument('password', type=str, required=True)
        pars.add_argument('id', type=int, required=True)
        pars.add_argument('name', type=str, required=False)
        pars.add_argument('admin_users', type=str, required=False, action='append')
        pars.add_argument('api_users', type=str, required=False, action='append')
        pars.add_argument('for_all', type=str, required=False)
        pars.add_argument('data_file', type=FileStorage, required=False, location='files')
        args = pars.parse_args()
        if args.login and args.password:
            user = User.query.filter_by(login=args.login).first()
            if user and check_password_hash(user.password, args.password):
                result['auth'] = True
                data = db.session.query(Classifier).filter(Classifier.id == args.id).scalar()
                if data and user.login in data.admin_users:
                    result['response'] = []
                    if args.name and generate.correct_login(args.name):
                        data.name = args.name
                        result['response'].append('name')
                    if args.admin_users:
                        data.admin_users.append(args.admin_users)
                        result['response'].append('admin_users')
                    if args.api_users:
                        data.api_users.append(args.api_users)
                        result['response'].append('api_users')
                    if args.for_all:
                        data.for_all = args.for_all
                        result['response'].append('for_all')
                    s = 'cl' if data.type == 'classify' else 'pa'
                    if args.data_file and generate.correct_file(args.data_file.filename, rule=s):
                        e, path = create_file(args, args.data_file)
                        if e:
                            result['response'].append(e)
                        else:
                            result['response'].append('data_file')
                    try:
                        db.session.merge(data)
                        db.session.flush()
                        db.session.commit()
                    except DatabaseError:
                        print("ОШИБКА КОМИТА")
                        result['response'].append('Ошибка бд')
                        db.session.rollback()
                else:
                    result['error'] = 'Ключ не найден или у вас нет доступа'
            else:
                result['error'] = 'Неверная комбинация логина/пароля'
        else:
            result['error'] = 'Неверная комбинация логина/пароля'
        return result

    # noinspection PyMethodMayBeStatic
    def delete(self):  # Запрос на удаление api
        result = {}
        pars = reqparse.RequestParser()
        pars.add_argument('login', type=str, required=True)
        pars.add_argument('password', type=str, required=True)
        pars.add_argument('id', type=int, required=True)
        args = pars.parse_args()
        if args.login and args.password:
            user = User.query.filter_by(login=args.login).first()
            if user and check_password_hash(user.password, args.password):
                result['auth'] = True
                data = Classifier.query.filter(Classifier.id == args.id).first()
                if data and user.login in data.admin_users:
                    Classifier.query.filter(Classifier.id == args.id).delete()
                    if user.classifiers[0] == str(args.id):
                        user.classifiers = user.classifiers[2:]
                    else:
                        user.classifiers = user.classifiers.replace(f'@{args.id}', '')
                    try:
                        db.session.merge(user)
                        db.session.flush()
                        db.session.commit()
                        result['response'] = 'Успешно'
                    except DatabaseError:
                        db.session.rollback()
                        result['response'] = 'Ошибка удаления'
                else:
                    result['response'] = 'Ошибка доступа'
        return result


api.add_resource(WaterDialog, '/api')
api.add_resource(WaterDialogSettings, '/api/settings')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(16), nullable=False, unique=True)
    password = db.Column(db.String(16), nullable=False)
    classifiers = db.Column(db.String(511), nullable=False)


class Classifier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    data_file = db.Column(db.String(255), nullable=False)
    admin_users = db.Column(db.PickleType, nullable=False)
    api_users = db.Column(db.PickleType, nullable=True)
    for_all = db.Column(db.Boolean, default=True, nullable=True)
    views = db.Column(db.Integer, default=0, nullable=True)
    type = db.Column(db.String(16), nullable=False)


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
    return render_template('login.html', t='Авторизация')


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
            # noinspection PyArgumentList
            n_user = User(login=log, password=h_pas, classifiers='')
            db.session.add(n_user)
            try:
                db.session.commit()
            except DatabaseError:
                db.session.rollback()
            return redirect(url_for('login'))
    return render_template('register.html', t='Регистрация')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    print(url_for('login'))
    if request.method == 'POST':
        return redirect(f"http://127.0.0.1:5000/new/{request.form['selector']}")
    a = db.session.query(User).filter(User.login == current_user.login)[0]
    if current_user.classifiers:
        print(a.classifiers)
        for i in current_user.classifiers:
            print(i)
        data = [Classifier.query.filter_by(id=i).first().name for i in current_user.classifiers.split('@')]
        print(data)
    else:
        data = []
    return render_template('menu.html', table=data)


@app.route('/api/config/<name>')
@login_required
def config(name):
    print(name)
    data = db.session.query(Classifier).filter(Classifier.name == name).scalar()
    print(data)
    if str(current_user.login) not in data.admin_users:
        return 'У вас недостаточно прав!'
    if data.api_users:
        data.api_users = [i[0] for i in data.api_users]
    return render_template('api_config.html', data_f=data)


@app.route('/api/docs')
def docs():
    return '1'


@app.route('/new/<typ>', methods=['GET', 'POST'])
@login_required
def new_classify(typ):
    if typ == 'classify':
        pattern_data = {
            'type': 'classify',
            'files': ['carbon.png', 'carbon2.png', 'carbon6.png'],
            'img': 'left: -160px;',
            'rule': 'cl'
        }
    elif typ == 'parser':
        pattern_data = {
            'type': 'parser',
            'files': ['carbon3.png', 'carbon4.png', 'carbon5.png'],
            'img': 'left: 80px;',
            'rlist': [],
            'rule': 'pa'
        }
        for i in os.listdir():
            pattern_data['rlist'].append(i.replace('.json', ''))
    else:
        return redirect('http://127.0.0.1:5000/menu')
    if request.method == 'POST':
        f = request.form.to_dict()
        fi = request.files['file']
        if f['login'] and fi:
            if generate.correct_login(f['login']):
                if generate.correct_file(fi.filename, rule=pattern_data['rule']):
                    args = generate.ArgsFile(current_user.login, f['login'], typ)
                    e, path = create_file(args, fi)
                    if e:
                        flash(e)
                    new_classifier = Classifier(
                        name=f['login'],
                        data_file=f'user_data/{current_user.login}/{pattern_data["type"]}/{f["login"]}',
                        admin_users=[current_user.login],
                        type=typ)
                    try:
                        db.session.add(new_classifier)
                    except DatabaseError:
                        print("ОШИБКА КОМИТА")
                        db.session.rollback()
                    new_classifier = db.session.query(Classifier).filter(Classifier.name == f['login']).first()
                    usr = db.session.query(User).filter(User.login == current_user.login).first()
                    if usr.classifiers != '':
                        usr.classifiers = f'{usr.classifiers}@{new_classifier.id}'
                    else:
                        usr.classifiers = str(new_classifier.id)
                    print(new_classifier.id)
                    print(usr.classifiers, '1--------')
                    try:
                        db.session.merge(usr)
                        db.session.flush()
                        db.session.commit()
                    except DatabaseError:
                        print("ОШИБКА КОМИТА")
                        db.session.rollback()
                    try:
                        fi.save(path)
                    except FileExistsError as e:
                        print("ОШИБКА СОХРАНЕНИЯ", e)
                    a = User.query.filter_by(login=current_user.login).first()
                    print(a.classifiers, '2--------')
                    return redirect(f'http://127.0.0.1:5000/api/config/{new_classifier.name}')
                else:
                    flash("Неверное заполнение файла данных")
            else:
                flash("Неверный формат логина(не больше 16 Английских букв)")
        else:
            flash("Введите имя api и загрузите .json")
    return render_template('new.html', data=pattern_data)


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
