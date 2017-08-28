from kazoo.client import KazooClient
from kazoo.exceptions import *


class Database:

    ADDRESS = "localhost:2182"

    def __init__(self):
        self.zk = KazooClient(hosts=Database.ADDRESS)
        self.zk.start()

    def append(self, topic, key, value, path="", ephemeral=False):
        try:
            self.zk.ensure_path("/"+topic+""+path)
            self.zk.create("/" + topic + "" + path + "/" + key, value.encode(),ephemeral=ephemeral)
        except NodeExistsError:
            self.zk.set("/" + topic + "" + path + "/" + key, value.encode())

    def get(self, topic, key, path=""):
        data = self.zk.get("/" + topic + "" + path + "/" + key)
        return data[0].decode()

    def set(self, topic, key, value, path=""):
        self.zk.set("/" + topic + "" + path + "/" + key, value.encode())

    def watch_on_lost(self, node_name, watcher):
        self.zk.get_children(node_name, watch=watcher)

    def get_nodes(self):
        return self.zk.get_children("/nodes")

    def get_ips(self):
        nodes = self.get_nodes()
        ips = []
        for node in nodes:
            ips.append(self.get("nodes", node))
        return ips

if __name__ == "__main__":
    database = Database()
    database.append("test", "key", "value")
    print(database.get("test", "key"))
