import datetime, json
from flask_restful import reqparse, abort, Api, Resource, request
from flask_cors import CORS
from flask import Flask, session ,render_template
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.json_util import dumps
from werkzeug.security import check_password_hash, generate_password_hash, safe_str_cmp
from flask_jwt_extended import (JWTManager, create_access_token, create_refresh_token, decode_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from bson.objectid import ObjectId
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


def auth(db):
    auth_header = request.headers.get('Authorization')
    auth_token = {}
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    token_user = decode_token(auth_token)
    user_id = token_user['identity']
    collection = db.users
    user = collection.find({'user_id': user_id})
    return user

def db_manager():
    client = MongoClient('mongodb://localhost:27017')
    db = client.pookle
    return db


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
        db = db_manager()
        collection = db.users
        users = dumps(collection.find())
        MongoClient('mongodb://localhost:27017').close()
        return users
    def post(self):
        args = parser.parse_args()
        user_id = args['user_id']
        user_pw = args['user_pw']
        user_que = args['user_que']
        user_ans = args['user_ans']
        db = db_manager()
        collection = db.users
        duplicate = dumps(collection.find({"user_id": user_id}))[1]
        if duplicate == '{':
            return "Duplicate accounts"
        user = {
            "user_id": user_id,
            "user_pw": generate_password_hash(user_pw),
            "user_que": user_que,
            "user_ans": generate_password_hash(user_ans),
            "user_nickname": user_id,
            "user_fav_timeline":[],
            "user_like_board":[],
            "user_comment":[],
            "user_fav_tag": [],
            "user_reg_date": datetime.datetime.now(),
            "user_last_date": datetime.datetime.now()
        }
        collection.insert(user).close()
        access_token = create_access_token(identity=user_id, expires_delta=False)
        refresh_token = create_refresh_token(identity=user_id, expires_delta=False)
        return {
            'message': 'User {} was created'.format(args['user_id']),
            'access_token': access_token,
            'refresh_token': refresh_token
        }

class UserDetail(Resource):
    def get(self):
        db = db_manager()
        collection = db.users
        user = auth(db)
        mongo_user = collection.find({'user_id': user[0]['user_id']})
        dict_user = json.loads(dumps(mongo_user))
        json_user = {
            "user_id": dict_user[0]['user_id'],
            "user_nickname" : dict_user[0]['user_nickname'],
            "user_fav_timeline" : dict_user[0]['user_fav_timeline'],
            "user_like_board" : dict_user[0]['user_like_board'],
            "user_fav_tag": dict_user[0]['user_fav_tag']
        }
        MongoClient('mongodb://localhost:27017').close()
        return json_user

class editNick(Resource):
    def put(self):
        parser.add_argument('nickname')
        args = parser.parse_args()
        new_nickname = args['nickname']
        db = db_manager()
        collection = db.users
        user = auth(db)
        collection.update(
            {'user_id': user[0]['user_id']},
            {'$set': {'user_nickname': new_nickname}}
        )
        MongoClient('mongodb://localhost:27017').close()




class changePasswd(Resource):
    def put(self):
        db = db_manager()
        collection = db.users
        user = auth(db)
        parser.add_argument('old_pw')
        parser.add_argument('new_pw')
        args = parser.parse_args()
        old_pw = args['old_pw']
        new_pw = args['new_pw']
        if check_password_hash(user[0]['user_pw'], old_pw):
            collection.update(
                {'user_id': user[0]['user_id']},
                {'$set': {'user_pw': generate_password_hash(new_pw)}}
            ).close()
            return 'success'
        else:
            MongoClient('mongodb://localhost:27017').close()
            return 'fail'

class favriteTag(Resource):
    def post(self):
        parser.add_argument('fav_tag')
        args = parser.parse_args()
        fav_tag = args['fav_tag']
        db = db_manager()
        collection = db.users
        user = auth(db)
        collection.update(
            {'user_id': user[0]['user_id']},
            {'$push': {'user_fav_tag': fav_tag}}
        )
        MongoClient('mongodb://localhost:27017').close()


    def put(self):
        parser.add_argument('fav_tag')
        args = parser.parse_args()
        fav_tag = args['fav_tag']
        db = db_manager()
        collection = db.users
        user = auth(db)
        collection.update(
            {'user_id': user[0]['user_id']},
            {'$pull': {'user_fav_tag': fav_tag}}
        )
        MongoClient('mongodb://localhost:27017').close()


class FavTimeline(Resource):
    def put(self):
        parser.add_argument('$oid')
        args = parser.parse_args()
        _id = args['$oid']
        db = db_manager()
        timeline_col = db.timeline
        user = auth(db)
        timeline_col.update(
            {'_id': ObjectId(_id)},
            {'$push':{
                'timeline_fav': {
                    'fav_user_id':user[0]['_id'],
                    'fav_user_name':user[0]['user_id']
                    }
                },
             '$inc': {'fav_cnt':1}
            }
        )



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
                    access_token = create_access_token(identity=args['user_id'], expires_delta=False)
                    refresh_token = create_refresh_token(identity=args['user_id'], expires_delta=False)
                    return {
                        'message': 'User {} was created'.format(args['user_id']),
                        'access_token': access_token,
                        'refresh_token': refresh_token
                    }
        MongoClient('mongodb://localhost:27017').close()
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
        return {'user_id': ''}


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user, expires_delta=False)
        return {'access_token': access_token}


class Timeline(Resource):
    def get(self):
        client = MongoClient('mongodb://localhost:27017')
        db = client.pookle
        collection = db.timeline
        timeline_posts = dumps(collection.find())
        client.close()
        return timeline_posts


class Board(Resource):
    def get(self):
        client = MongoClient('mongodb://localhost:27017')
        db = client.pookle
        collection = db.board
        board_posts = dumps(collection.find())
        client.close()
        return board_posts
    def post(self):
        return 0


api.add_resource(UserList, '/users')
api.add_resource(UserDetail,'/user')
api.add_resource(editNick,'/user/nick')
api.add_resource(changePasswd, '/user/pw')
api.add_resource(favriteTag, '/user/fav-tag')
api.add_resource(Login, '/user/login')
api.add_resource(MongoList, '/list')
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')
api.add_resource(Auth, '/auth')
api.add_resource(Board, '/board')
api.add_resource(Timeline, '/timeline')
api.add_resource(FavTimeline, '/timeline/fav')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')