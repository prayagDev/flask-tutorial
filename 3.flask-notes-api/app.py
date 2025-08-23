from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///note.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------- MODEL --------------------
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(1024))
    content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)


# -------------------- SCHEMA --------------------
class NoteSchema(SQLAlchemyAutoSchema):
    
    class Meta:
        model = Note
        load_instance = True
        include_fk = True

@app.route("/notes", methods=["GET", "POST", "PUT", "DELETE"])
def notes():
    if request.method == "GET":
        queryset = Note.query.filter_by(is_active=True)
        if request.args.get("id"):
            queryset = queryset.filter_by(id=request.args.get("id"))
        return jsonify(NoteSchema(many=True).dump(queryset))
    elif request.method == "POST":
        request_data = request.get_json()
        errors = NoteSchema(session=db.session).validate(data=request_data)
        if errors:
            return jsonify(errors), 400
        instance = NoteSchema().load(request_data, session=db.session)
        db.session.add(instance)
        db.session.commit()
        return jsonify(NoteSchema().dump(instance)), 201
    elif request.method == "PUT":
        request_data = request.get_json()
        if not request_data.get("id"):
            return jsonify({"detail": "ID is required"}), 400
        instance = Note.query.filter_by(id=request_data.get("id"), is_active=True).first()
        if not instance:
            return jsonify({"detail": "Note not found"}), 400
        errors = NoteSchema(session=db.session).validate(data=request_data)
        if errors:
            return jsonify(errors), 400
        instance = NoteSchema().load(request_data, instance=instance, session=db.session)
        db.session.commit()
        return jsonify(NoteSchema().dump(instance)), 201
    elif request.method == "DELETE":
        request_data = request.get_json()
        if not request_data.get("id"):
            return jsonify({"detail": "ID is required"}), 400
        instance = Note.query.filter_by(id=request_data.get("id"), is_active=True).first()
        if not instance:
            return jsonify({"detail": "Note not found"}), 400
        instance.is_active = False
        db.session.commit()
        return jsonify({"detail": "Note deleted (soft delete)"})
    return "Invalid Method"
    

# -------------------- RUN --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)