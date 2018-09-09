from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
from flask import Flask, session ,render_template
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.json_util import dumps
from werkzeug.security import check_password_hash, generate_password_hash, safe_str_cmp
from flask_jwt_extended import (JWTManager, create_access_token, create_refresh_token, decode_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
app = Flask(__name__)
CORS(app)
api = Api(app)
app.config.from_mapping(
    SECRET_KEY='dev',
)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
jwt = JWTManager(app)
mongo = PyMongo(app)

TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))

parser = reqparse.RequestParser()
parser.add_argument('user_id')
parser.add_argument('user_pw')
parser.add_argument('user_que')
parser.add_argument('user_ans')
parser.add_argument('access_token')



# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def post(self, todo_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS[todo_id] = task
        return task, 201


# TodoList
# shows a list of all todos, and lets you POST to add new tasks
class TodoList(Resource):
    def get(self):
        return TODOS

    def post(self):
        args = parser.parse_args()
        todo_id = int(max(TODOS.keys()).lstrip('todo')) + 1
        todo_id = 'todo%i' % todo_id
        TODOS[todo_id] = {'task': args['task']}
        return TODOS[todo_id], 201

class MongoList(Resource):
    def get(selfsel):
        client = MongoClient('mongodb://localhost:27017')
        db = client.test
        collection = db.test1
        results = dumps(db.test1.find())
        client.close()
        return results

class UserList(Resource):
    def get(self):
        client = MongoClient('mongodb://localhost:27017')
        db = client.pookle
        collection = db.users
        users = dumps(collection.find())
        client.close()
        return users
    def post(self):
        args = parser.parse_args()
        user_id = args['user_id']
        user_pw = args['user_pw']
        user_que = args['user_que']
        user_ans = args['user_ans']
        client = MongoClient('mongodb://localhost:27017')
        db = client.pookle
        collection = db.users
        collection.insert({"user_id": user_id, "user_pw": generate_password_hash(user_pw), "user_que": user_que, "user_ans": user_ans})
        client.close()
        access_token = create_access_token(identity=args['user_id'])
        refresh_token = create_refresh_token(identity=args['user_id'])
        return {
            'message': 'User {} was created'.format(args['user_id']),
            'access_token': access_token,
            'refresh_token': refresh_token
        }


class Login(Resource):
    def post(self):
        args = parser.parse_args()
        client = MongoClient('mongodb://localhost:27017')
        db = client.pookle
        collection = db.users
        users = collection.find()
        user_id = args['user_id']
        user_pw = args['user_pw']
        for user in users:
            if user['user_id'] == user_id:
                if check_password_hash(user['user_pw'], user_pw):
                    client.close()
                    access_token = create_access_token(identity=args['user_id'])
                    refresh_token = create_refresh_token(identity=args['user_id'])
                    return {
                        'message': 'User {} was created'.format(args['user_id']),
                        'access_token': access_token,
                        'refresh_token': refresh_token
                    }
        client.close()
        return False

class Auth(Resource):
    def post(self):
        args = parser.parse_args()
        access_token = args['access_token']
        user_id = decode_token(access_token)['identity']
        client = MongoClient('mongodb://localhost:27017')
        db = client.pookle
        collection = db.users
        users = collection.find()
        for user in users:
            if user['user_id'] == user_id:
                current_user = {
                    'user_id': user['user_id'],
                }
                return current_user
        return {'authentication':False}

class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user)
        return {'access_token': access_token}

api.add_resource(UserList, '/users')
api.add_resource(Login, '/user/login')
api.add_resource(MongoList, '/list')
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')
api.add_resource(Auth, '/auth')



if __name__ == '__main__':
    app.run(debug=True)