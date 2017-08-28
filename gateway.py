from http.server import *
from http.client import *
from data.accounts import *
import json
import sys
from util import hash
from Crypto.PublicKey import RSA
from annotation.singleton import singleton
from util.cipher import Cipher
import random

@singleton
class GatewayConfiguration:

    def __init__(self, **encryption_func):
        self.client_pub_key = None
        pair = RSA.generate(1024)
        self.server_pub_key = pair.publickey().exportKey()
        self.server_pri_key = pair.exportKey()
        self.symmetric_key = None
        self.encryption_function = encryption_func

        self.zookeeper_nodes = ["node1", "node2", "node3"]


class GatewayHandler(SimpleHTTPRequestHandler, BaseHTTPRequestHandler):

    account = Account()
    conf = GatewayConfiguration()
    db = Database()

    def do_GET(self):
        body = b""
        while True:
            line = self.rfile.readline()
            if line is None or len(line) == 0 or line == b"\0\n":
                break
            body += line
        body = body.strip(b'\n')
        header_dic = dict(x for x in self.headers.items())

        destination = header_dic.get("Destination")
        url = header_dic.get("URL")

        if self.path == "/forward" and not self._validate_authentication(header_dic["Authentication"]):
            self._respond(401, "unauthorized")
            return

        if self.path == "/forward":
            print("receive message: "+str(body))
            body = self._decrypt(body)
        body = body.decode("ascii")
        print("receive message decrypted: " + body)

        response = {}
        try:
            if self.path == "/register":
                body_json = json.loads(body)
                response = self.register(body_json)
            elif self.path == "/forward":
                response = self.forward("GET", url, body, header_dic)
            elif self.path == "/key":
                body_json = json.loads(body)
                response = self.exchange_keys(body_json)
        except HTTPException as e:
            response = {"ret": "server error"}
            print(e)
            self._respond(500, response)
            return
        if "Authentication" in header_dic:
            self._update_passsword(header_dic["Authentication"])
        self._respond(200, response)

    def forward(self, method, url, body, headers):
        ips = self.db.get_ips()
        ip = random.choice(ips)
        conn = HTTPConnection(ip)
        conn.request(method, url, body + ("\n\0\n" if type(body) is str else b"\n\0\n"), headers)
        response = conn.getresponse()
        conn.close()
        return json.loads(response.read().decode("ascii"))

    def register(self, body):
        print("register successfully")
        print("[username] "+body['name'])
        print("[password] "+body['password'])

        # save into database
        self.account.set_password(body['name'], body['password'])
        return {"ret": "success"}

    def exchange_keys(self, body):
        if body["mode"] == "symmetric":
            self.conf.symmetric_key = body["key"].encode()
            return {"key": body["key"]}
        elif body["mode"] == "asymmetric":
            self.conf.client_pub_key = body["key"].encode()
            return {"key": self.conf.server_pub_key.decode("ascii")}

    def _validate_authentication(self, authentication):
        username, password = str.split(hash.base64decode(authentication), "-")
        return self.account.validate(username, password)

    def _update_passsword(self, authentication):
        username, password = str.split(hash.base64decode(authentication), "-")
        return self.account.set_password(username, password)

    def _respond(self, code, body):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _encrypt(self, text):
        if self.conf.encryption_function.is_symmetric:
            return self.conf.encryption_function.encrypt(self.conf.symmetric_key, text)
        else:
            return self.conf.encryption_function.encrypt(self.conf.client_pub_key, text)

    def _decrypt(self, text):
        if self.conf.encryption_function.is_symmetric:
            return self.conf.encryption_function.decrypt(self.conf.symmetric_key, text)
        else:
            return self.conf.encryption_function.decrypt(self.conf.server_pri_key, text)


class Gateway(HTTPServer):

    def __init__(self, encryption_function):
        self.server_socket = None
        self.conf = GatewayConfiguration()
        self.conf.encryption_function = encryption_function

    def run(self, server_class=HTTPServer, handler_class=GatewayHandler):
        server_address = ('', 80)
        httpd = server_class(server_address, handler_class)
        db = Database()

        def on_lost(event):
            nodes = db.get_nodes()
            for node in self.conf.zookeeper_nodes:
                if node not in nodes:
                    print("zookeeper node ({}) is lost, recover from other nodes".format(node))
            db.watch_on_lost("/nodes", on_lost)

        db.watch_on_lost("/nodes", on_lost)
        httpd.serve_forever()


if __name__ == "__main__":
    algorithm_map = {
        "RC2": Cipher.RC2,
        "DES": Cipher.DES,
        "RSA": Cipher.RSA
    }
    argv = sys.argv
    if len(argv) != 2:
        print("wrong argument number")
    gateway = Gateway(algorithm_map.get(argv[1]))
    gateway.run()
