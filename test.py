from pymongo import MongoClient
uri = ""
client = MongoClient(uri)
print(client.list_database_names())
