from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user


# -- Set up Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'KJSDFGJHFVREFKUYGFALEJREGL36289HJFW'

# -- Set up DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Bootstrap(app)

# -- Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return db.session.get(entity=User, ident=int(user_id))

# -- Set up tables in DB
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    list = relationship('Goals', back_populates='author')

class Goals(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates='list')


with app.app_context():
    db.create_all()

goals = []
# -- Set uo routes
@app.route('/', methods=['GET', "POST"])
def home():
    if not current_user.is_authenticated:
        if request.method == "POST":
            goals.append(request.form['goal'])
            print(goals)
            return redirect(url_for('home'))
    else:
        existing_goals = db.session.execute(db.select(Goals).filter_by(user_id=current_user.id)).scalars()
        if request.method == "POST" and request.form['goal'] != '':
            gl = request.form['goal']
            print(gl)
            new_goal = Goals(
                goal=gl,
                user_id=current_user.id,
            )
            db.session.add(new_goal)
            db.session.commit()
            return redirect(url_for('home'))
        return render_template('index.html', logged_in=current_user.is_authenticated, current_user=current_user,
                               goals=goals, existing_goals=existing_goals)
    return render_template('index.html', logged_in=current_user.is_authenticated, current_user=current_user,
                           goals=goals)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        try:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Wrong password!")
                return redirect(url_for('login'))
        except AttributeError:
            flash('No such email in db')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        if not user:
            new_user = User(
                name=request.form['name'],
                email=email,
                password=generate_password_hash(
                    password=request.form['password'],
                    method='pbkdf2:sha256',
                    salt_length=8),
            )

            db.session.add(new_user)
            db.session.commit()

            # Log in and authenticate user after adding details to database.
            login_user(new_user)

            return redirect(url_for('home'))
        else:
            error = 'This email is already registered, please log in'
            return render_template('login.html', error=error)

    return render_template('register.html')

@app.route('/delete/<int:goal_id>')
def delete(goal_id):
    if not current_user.is_authenticated:
        goals.pop(goal_id)
        return redirect(url_for('home'))
    else:
        goal_to_delete = db.session.execute(db.select(Goals).filter_by(id=goal_id)).scalar()
        db.session.delete(goal_to_delete)
        db.session.commit()
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
