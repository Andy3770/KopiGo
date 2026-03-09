from pymongo import MongoClient
uri = "mongodb://kopigoadmin:kopigopassword@ac-1dsypwv-shard-00-00.47bjtm9.mongodb.net:27017,ac-1dsypwv-shard-00-01.47bjtm9.mongodb.net:27017,ac-1dsypwv-shard-00-02.47bjtm9.mongodb.net:27017/KopiGo?ssl=true&replicaSet=atlas-ljxhqg-shard-0&authSource=admin&retryWrites=true&w=majority"
client = MongoClient(uri)
print(client.list_database_names())
