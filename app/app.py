from flask import Flask, request, jsonify, make_response, render_template
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'false'


db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	public_id = db.Column(db.String(50), unique=True)
	name = db.Column(db.String(50))
	password = db.Column(db.String(80))
	admin = db.Column(db.Boolean)

def tokin_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None

		if 'x-access-token' in request.headers:
			token = request.headers['x-access-token']

		if not token:
			return jsonify({'message' : 'token is missing'}), 401

		try:
			data = jwt.decode(token, app.config['SECRET_KEY'])
			current_user = User.query.filter_by(public_id=data['public_id']).first()
		except:
			return jsonify({'message': 'token is invalid'}), 401

		return f(current_user, *args, **kwargs)

	return decorated

class Todo(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	text = db.Column(db.String(50))
	complete = db.Column(db.Boolean)
	user_id = db.Column(db.Integer)

@app.route('/')
def index():
	return "Hello World"

@app.route('/user', methods=['GET'])
@tokin_required
def get_all_users(current_user):

	if not current_user.admin:
		return jsonify({'message' : 'Cannot preform that function'})

	users = User.query.all()
	output=[]

	for user in users:
		user_data = {}
		user_data['public_id'] = user.public_id
		user_data['name'] = user.name
		user_data['password'] = user.password
		user_data['admin'] = user.admin
		output.append(user_data)

	return jsonify({'users' : output})
@app.route('/user/<public_id>', methods=['GET'])
def get_one_user(public_id):
	if not current_user.admin:
		return jsonify({'message' : 'Cannot preform that function'})

	user = User.query.filter_by(public_id=public_id).first()

	if not user:
		return jsonify({'message' : 'No user found'})

	user_data = {}
	user_data['public_id'] = user.public_id
	user_data['name'] = user.name
	user_data['password'] = user.password
	user_data['admin'] = user.admin

	return jsonify({'user' : user_data})

@app.route('/user', methods=['POST'])
@tokin_required
def create_user(current_user):
	if not current_user.admin:
		return jsonify({'message' : 'Cannot preform that function'})

	data = request.get_json()
	print('hello')
	hashed_password = generate_password_hash(data['password'], method='sha256')
	new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
	db.session.add(new_user)
	db.session.commit()
	return jsonify({'message' : 'New user created'})

@app.route('/user/<public_id>', methods=['PUT'])
@tokin_required
def promote_user(current_user, public_id):
	if not current_user.admin:
		return jsonify({'message' : 'Cannot preform that function'})

	user = User.query.filter_by(public_id=public_id).first()

	if not user:
		return jsonify({'message' : 'No user found!'})

	user.admin = True
	db.session.commit()

	return jsonify ({'message' : 'User has been promoted'})

@app.route('/user/<public_id>', methods=['DELETE'])
@tokin_required
def delete_user(current_user, public_id):
	if not current_user.admin:
		return jsonify({'message' : 'Cannot preform that function'})

	user = User.query.filter_by(public_id=public_id).first()

	if not user:
		return jsonify({'message' : 'No user found!'})

	db.session.delete(user)
	db.session.commit()
	return jsonify({'message' : 'User deleted'})

@app.route('/login')
def login():
	auth = request.authorization

	if not auth or not auth.username or not auth.password:
		return make_response('could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

	user = User.query.filter_by(name=auth.username).first()

	if not user:
		return make_response('could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

	if check_password_hash(user.password, auth.password):
		token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

		return jsonify({'token' : token.decode('UTF-8')})

	return make_response('could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

@app.route('/todo', methods=['GET'])
@tokin_required
def get_all_todos(current_user):
	todos = Todo.query.filter_by(user_id=current_user.id).all()

	output = []

	for todo in todos:
		todo_data = {}
		todo_data['id'] = todo.id
		todo_data['text'] = todo.text
		todo_data['complete'] = todo.complete
		output.append(todo_data)

	return jsonify({'todos' : output})

@app.route('/todo/<todo_id>', methods=['GET'])
@tokin_required
def get_one__todo(current_user, todo_id):
	return ''

@app.route('/todotest')
def hello():
	todos = Todo.query.all()
	return render_template('index.html', todos=todos)

@app.route('/todo', methods=['POST'])
@tokin_required
def create_todo(current_user):
	data = request.get_json()

	new_todo = Todo(text=data['text'], complete=False, user_id=current_user.id)
	db.session.add(new_todo)
	db.session.commit()
	return jsonify({'message' : 'Todo created'})

@app.route('/todo/<todo_id>', methods=['PUT'])
@tokin_required
def complete_todo(current_user, todo_id):
	return ''

@app.route('/todo/<todo_id>', methods=['DELETE'])
@tokin_required
def delete_todo(current_user, todo_id):
	return ''


if __name__=='__main__':
	app.run(debug=True)