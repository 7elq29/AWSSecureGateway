from http.server import *
from data.simpledata import *
from data.database import *
import json
import ipaddress


database = SimpleData()

class HTTPHandler(SimpleHTTPRequestHandler, BaseHTTPRequestHandler):

    def do_GET(self):
        body = b""
        while True:
            line = self.rfile.readline()
            if line is None or len(line) == 0 or line == b"\0\n":
                break
            body += line
        body = body.decode("ascii")

        if self.path == "/echo":
            print("[print headers]:" + ''.join(str(x) for x in self.headers.items()))
            print("[print path]:" + self.path)
            print("[print body]:" + body)
            self._respond(200, {"ret": "success"})
        elif self.path == "/put":
            data = json.loads(body)
            database.set_data(data["key"], data["value"])
            self._respond(200, {"ret": "success"})
            print("data saved: {{key: {}, value: {}}}".format(data["key"], data["value"]))
        elif self.path == "/get":
            data = json.loads(body)
            value = database.get_data(data["key"])
            self._respond(200, {"ret": "success", "value": value})
            print("get data: {{key: {}, value: {}}}".format(data["key"], value))
        else:
            self._respond(200, {"ret": "wrong path"})

    def _respond(self, code, body):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())


class Server(HTTPServer):

    def __init__(self):
        self.server_socket = None
        self.port = 80
        self.ip = "10.1.0.33"

    def run(self, server_class=HTTPServer, handler_class=HTTPHandler):
        server_address = ('', self.port)
        self.register_server()
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()


    def register_server(self):
        db = Database()
        db.append("nodes", "node1", self.ip + ":" + str(self.port), ephemeral=True)


if __name__ == "__main__":
    server = Server()
    server.run()

