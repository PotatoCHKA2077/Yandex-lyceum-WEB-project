from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.users import User
from data.notes import Notes
from forms.notes import NotesForm
from forms.loginform import LoginForm
from forms.user import RegisterForm
import os
import shutil

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def main():
    db_session.global_init("db/notes.sqlite")
    app.run(port=8080, host='127.0.0.1')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    images = {}
    videos = {}
    if current_user.is_authenticated:
        notes = db_sess.query(Notes).filter(Notes.user == current_user)
        for note in notes:
            images[note.title] = os.listdir(f'static/users_file/{note.user_id}/images/{note.title}/')
            videos[note.title] = os.listdir(f'static/users_file/{note.user_id}/videos/{note.title}/')

    else:
        note = Notes()
        note.title = 'Необходимо авторизироваться на сайте'
        note.content = ('Пожалуйста войдите в свой аккаунт, или если вы впервые на этом сайте зарегестрируйтесь'
                            ' и войдите в новый аккаунт')
        notes = [note]
    return render_template("index.html", notes=notes, images=images, videos=videos, title='MyMemories')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким email уже есть")
        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/notes',  methods=['GET', 'POST'])
@login_required
def add_notes():
    form = NotesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Notes).filter(Notes.title == form.title.data, Notes.user == current_user).first():
            return render_template('notes.html', title='Добавление новости',
                                   form=form, message="Запись с таким заголовком уже существует")
        notes = Notes()
        notes.title = form.title.data
        notes.content = form.content.data
        notes.user_id = current_user.id
        if request.method == 'POST':
            # сохраняем файл
            dir_path = f'static/users_file/{current_user.id}/'
            if str(current_user.id) not in os.listdir('static/users_file'):
                os.mkdir(dir_path)
            images = request.files.getlist('image')
            if 'images' not in os.listdir(dir_path):
                os.mkdir(f'{dir_path}images/')
            if notes.title not in os.listdir(f'{dir_path}images/'):
                os.mkdir(f'{dir_path}images/{notes.title}')
            for image in images:
                if image:
                    filename = secure_filename(image.filename)
                    image.save(f'{dir_path}images/{notes.title}/{filename}')

            videos = request.files.getlist('video')
            if 'videos' not in os.listdir(dir_path):
                os.mkdir(f'{dir_path}videos/')
            if notes.title not in os.listdir(f'{dir_path}videos/'):
                os.mkdir(f'{dir_path}videos/{notes.title}')
            for video in videos:
                if video:
                    filename = secure_filename(video.filename)
                    video.save(f'{dir_path}videos/{notes.title}/{filename}')
        try:
            current_user.notes.append(notes)
        except Exception as ex:
            print(ex)
            return render_template('notes.html', title='Добавление новости', form=form,
                                   message='Извитните, произошла непредвиденная ошибка!'
                                           ' Просим вас нажать на кнопку "Создать" снова '
                                           '(Выбирать файлы повторно не нужно).')
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('notes.html', title='Добавление новости',
                           form=form)


@app.route('/notes/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_notes(id):
    form = NotesForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        notes = db_sess.query(Notes).filter(Notes.id == id, Notes.user == current_user).first()
        if notes:
            form.title.data = notes.title
            form.content.data = notes.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        notes = db_sess.query(Notes).filter(Notes.id == id,
                                            Notes.user == current_user
                                            ).first()
        if notes:
            if request.method == 'POST':
                # сохраняем файл
                dir_path = f'static/users_file/{current_user.id}/'
                if str(current_user.id) not in os.listdir('static/users_file'):
                    os.mkdir(dir_path)
                images = request.files.getlist('image')
                if 'images' not in os.listdir(dir_path):
                    os.mkdir(f'{dir_path}images/')
                if notes.title not in os.listdir(f'{dir_path}images/'):
                    os.mkdir(f'{dir_path}images/{notes.title}')
                for image in images:
                    if image:
                        filename = secure_filename(image.filename)
                        image.save(f'{dir_path}images/{notes.title}/{filename}')

                videos = request.files.getlist('video')
                if 'videos' not in os.listdir(dir_path):
                    os.mkdir(f'{dir_path}videos/')
                if notes.title not in os.listdir(f'{dir_path}videos/'):
                    os.mkdir(f'{dir_path}videos/{notes.title}')
                for video in videos:
                    if video:
                        filename = secure_filename(video.filename)
                        video.save(f'{dir_path}videos/{notes.title}/{filename}')
            notes.title = form.title.data
            notes.content = form.content.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('notes.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/notes_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def notes_delete(id):
    db_sess = db_session.create_session()
    notes = db_sess.query(Notes).filter(Notes.id == id,
                                        Notes.user == current_user
                                        ).first()
    if notes:
        shutil.rmtree(f'static/users_file/{notes.user_id}/{notes.title}/')
        db_sess.delete(notes)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


if __name__ == '__main__':
    main()
