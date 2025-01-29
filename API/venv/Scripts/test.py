from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from sqlalchemy.exc import IntegrityError
import os

# Initialisation de l'application Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_app.db'  # SQLite configuration
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Modèle utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

# Formulaire d'inscription
class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                     validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

# Formulaire de connexion
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[InputRequired()])
    submit = SubmitField('Se connecter')

# Route principale
@app.route('/')
def home():
    return render_template('home.html', logged_in=('user_id' in session))

# Route pour l'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Compte créé avec succès ! Connectez-vous.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Le nom d\'utilisateur ou l\'email existe déjà.', 'danger')
    return render_template('register.html', form=form)

# Route pour la connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Connexion réussie !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants invalides.', 'danger')
    return render_template('login.html', form=form)

# Route pour le tableau de bord
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# Route pour la déconnexion
@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('home'))

# Fonction pour s'assurer que le dossier templates existe et écrire les fichiers HTML
TEMPLATES_DIR = os.path.join(os.getcwd(), 'templates')
os.makedirs(TEMPLATES_DIR, exist_ok=True)

def create_template(filename, content):
    filepath = os.path.join(TEMPLATES_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True)