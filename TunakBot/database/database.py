from pymongo import MongoClient

# TODO make this a class

db = None


def init(host='localhost', port=27017):
    global db
    client = MongoClient(host, port)
    db = client['tunak_database']
