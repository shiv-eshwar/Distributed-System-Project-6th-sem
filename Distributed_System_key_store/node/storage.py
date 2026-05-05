# node/storage.py

class KeyValueStore:
    def __init__(self):
        self.store = {}

    def put(self, key, value):
        self.store[key] = value
        return "Stored successfully"

    def get(self, key):
        return self.store.get(key, "Key not found")

    def get_all(self):
        return self.store