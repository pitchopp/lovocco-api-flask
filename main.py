import re
from flask import Flask, jsonify, request
import json
from datetime import datetime
from pymongo import MongoClient
import pymongo
from bson.objectid import ObjectId


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)
app.json_encoder = JSONEncoder


def get_db() -> pymongo.database.Database:
    client = MongoClient(port=27017)
    return client.lovocco


@app.route("/<string:collection>/<string:index>", methods=['GET', 'PUT'])
def user(collection, index):
    if request.method == 'GET':
        db = get_db()
        return add_headers(jsonify(db[collection].find_one({'_id': ObjectId(index)})))
    elif request.method == 'PUT':
        db = get_db()
        result = db[collection].update_one({'_id': ObjectId(index)}, {"$set": request.get_json(force=True)}, upsert=False)
        return add_headers(jsonify({'status': 'OK', 'count': result.modified_count}))


def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/<string:collection>", methods=['POST', 'GET', 'PUT'])
def insert_user(collection):
    if request.method == 'POST':
        db = get_db()
        body = request.get_json(force=True)
        result = db[collection].insert_one(body)
        return add_headers(jsonify({'_id': result.inserted_id, 'status': 'OK'}))
    if request.method == 'PUT':
        db = get_db()
        body = request.get_json(force=True)
        result = db[collection].insert_one(body)
        return add_headers(jsonify({'_id': result.inserted_id, 'status': 'OK'}))
    if request.method == 'GET':
        db = get_db()
        args = dict(request.args)
        results = db[collection].find(args)
        response = jsonify(list(results))
        return add_headers(response)


@app.route("/register", methods=['PUT'])
def register():
    if request.method == 'PUT':
        body = dict(request.get_json(force=True))
        email = body.get('email')
        password = body.get('password')
        if not re.match("[^@]+@[^@]+\.[^@]+", email):
            return add_headers(jsonify({"status": "KO", "message": "invalid email format"}))
        if password in ['', None]:
            return add_headers(jsonify({"status": "KO", "message": "invalid password"}))
        db = get_db()
        if db.users.find_one({"email": email}):
            return add_headers(jsonify({"status": "KO", "message": "email already exists"}))
        result = db.users.insert_one({"email": email, "password": password, "createdAt": datetime.now()})
        return add_headers(jsonify({"status": "OK", "token": result.inserted_id}))


@app.route("/authenticate", methods=['POST'])
def authenticate():
    if request.method == 'POST':
        db = get_db()
        body = dict(request.get_json(force=True))
        email = body.get('email')
        password = body.get('password')
        result = db.users.find_one({"email": email, "password": password})
        if result is None:
            return add_headers(jsonify({"status": "KO"}))
        return add_headers(jsonify({"token": result.get('_id')}))


if __name__ == "__main__":
    app.run(host='0.0.0.0')
