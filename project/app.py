import os
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
    abort,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy

basedir = Path(__file__).resolve().parent

# configuration
DATABASE = "flaskr.db"
USERNAME = "admin"
PASSWORD = "admin"
SECRET_KEY = "change_me"
url = os.getenv("DATABASE_URL", f"sqlite:///{Path(basedir).joinpath(DATABASE)}")

if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = url
SQLALCHEMY_TRACK_MODIFICATIONS = False

# create and initialize a new Flask app
app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)

from project import models

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.")
            return jsonify({"status": 0, "message": "Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    entries = db.session.query(models.Post)
    return render_template("index.html", entries=entries)

@app.route("/add", methods=["POST"])
def add_entry():
    if not session.get("logged_in"):
        abort(401)
    new_entry = models.Post(request.form["title"], request.form["text"])
    db.session.add(new_entry)
    db.session.commit()
    flash("New entry was successfully posted")
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] != app.config["USERNAME"]:
            error = "Invalid username"
        elif request.form["password"] != app.config["PASSWORD"]:
            error = "Invalid password"
        else:
            session["logged_in"] = True
            flash("You were logged in")
            return redirect(url_for("index"))
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You were logged out")
    return redirect(url_for("index"))

@app.route("/delete/<int:post_id>", methods=["GET"])
@login_required
def delete_entry(post_id):
    result = {"status": 0, "message": "Error"}
    try:
        db.session.query(models.Post).filter_by(id=post_id).delete()
        db.session.commit()
        result = {"status": 1, "message": "Post Deleted"}
        flash("The entry was deleted.")
    except Exception as e:
        result = {"status": 0, "message": repr(e)}
    return jsonify(result)

@app.route("/search/", methods=["GET"])
def search():
    query = request.args.get("query")
    entries = db.session.query(models.Post)
    if query:
        return render_template("search.html", entries=entries, query=query)
    return render_template("search.html")

# === REST API for Notes ===

@app.route("/api/notes", methods=["GET"])
def get_notes():
    notes = db.session.query(models.Note).all()
    return jsonify([note.to_dict() for note in notes]), 200

@app.route("/api/notes/<int:note_id>", methods=["GET"])
def get_note(note_id):
    note = db.session.get(models.Note, note_id)
    if note:
        return jsonify(note.to_dict()), 200
    return jsonify({"error": "Note not found"}), 404

@app.route("/api/notes", methods=["POST"])
def create_note():
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400
    note = models.Note(content=data["content"])
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    note = db.session.get(models.Note, note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400
    note.content = data["content"]
    db.session.commit()
    return jsonify(note.to_dict()), 200

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    note = db.session.get(models.Note, note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"}), 200

if __name__ == "__main__":
    app.run()
