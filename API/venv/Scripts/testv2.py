from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_app.db'
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
    role = db.Column(db.String(20), nullable=False)  # admin, professeur, eleve

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[InputRequired(), EqualTo('password')])
    role = SelectField('Rôle', choices=[('eleve', 'Élève'), ('professeur', 'Professeur')], validators=[InputRequired()])  # Suppression de l'option admin
    submit = SubmitField('S\'inscrire')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.role.data == 'admin' and User.query.filter_by(role='admin').first():
            flash('Un administrateur existe déjà.', 'danger')
            return redirect(url_for('index'))
        
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role=form.role.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Compte créé avec succès !', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Le nom d\'utilisateur ou l\'email existe déjà.', 'danger')
    return render_template('index.html', form=form)  # Utilisation de la page fournie

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role  # Stocke le rôle dans la session
            flash('Connexion réussie !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects.', 'danger')
    return render_template('index.html')  # Utilisation de la page fournie

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Veuillez vous connecter.', 'danger')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        students = User.query.filter_by(role='eleve').all()
        teachers = User.query.filter_by(role='professeur').all()
        return render_template('admin.html', students=students, teachers=teachers)  # Redirection vers la page admin
    elif user.role == 'professeur':
        students = User.query.filter_by(role='eleve').all()
        return render_template('prof.html', students=students)  # Redirection vers la page professeur
    elif user.role == 'eleve':
        return render_template('student.html', student=user)  # Redirection vers la page élève
    else:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role='admin').first():  # Création d'un seul admin si inexistant
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = User(username='admin', email='admin@example.com', password_hash=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
