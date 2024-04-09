from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from data.notes import Notes
from forms.notes import NotesForm
from forms.loginform import LoginForm
from forms.user import RegisterForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def main():
    db_session.global_init("db/notes.sqlite")
    app.run()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        notes = db_sess.query(Notes).filter(Notes.user == current_user)
    else:
        note = Notes()
        note.title = 'Необходимо авторизироваться на сайте'
        note.content = ('Пожалуйста войдите в свой аккаунт, или если вы впервые на этом сайте зарегестрируйтесь'
                            ' и войдите в новый аккаунт')
        notes = [note]
    return render_template("index.html", notes=notes)


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
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
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
        notes = Notes()
        notes.title = form.title.data
        notes.content = form.content.data
        notes.file = form.file.data
        current_user.notes.append(notes)
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
        notes = db_sess.query(Notes).filter(Notes.id == id,
                                            Notes.user == current_user
                                            ).first()
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
        db_sess.delete(notes)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


if __name__ == '__main__':
    main()
