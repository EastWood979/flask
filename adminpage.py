from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# Initialisation de l'application Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin_example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'  # Nécessaire pour Flask-Admin

# Initialisation de la base de données
db = SQLAlchemy(app)

# Modèle User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Ajout d'une vue admin pour le modèle User
class UserAdmin(ModelView):
    column_list = ('id', 'username', 'email')  # Colonnes affichées dans l'admin
    form_columns = ('username', 'email')  # Colonnes modifiables

# Configuration de Flask-Admin
admin = Admin(app, name='Mon Admin', template_mode='bootstrap4')
admin.add_view(UserAdmin(User, db.session))

# Point de départ
@app.route('/')
def home():
    return "<h1>Bienvenue sur la page principale</h1><p>Accédez à l'admin : /admin</p>"

# Création des tables et lancement de l'app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables dans la base de données
    app.run(debug=True)
