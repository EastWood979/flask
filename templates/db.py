from flask import Flask, render_template, request, g
import sqlite3

app = Flask(__name__)
DATABASE = "projet_school.db"  # Chemin vers ta base de données SQLite

def get_db():
    """Connexion à la base de données"""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Permet d’accéder aux colonnes par leur nom
    return db

@app.route("/")
def index():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM voitures")  # Remplace 'voitures' par le nom de ta table
    voitures = cur.fetchall()
    return render_template("index.html", voitures=voitures)

@app.teardown_appcontext
def close_connection(exception):
    """Fermer la connexion après chaque requête"""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)
