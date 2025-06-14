from project.app import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)

    def __init__(self, title, text):
        self.title = title
        self.text = text

    def __repr__(self):
        return f"<title {self.title}>"


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)

    def __init__(self, content):
        self.content = content

    def to_dict(self):
        return {"id": self.id, "content": self.content}
