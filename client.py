import json
from http.client import *
from util import hash
from util.otputil import *
from util.cipher import Cipher
import http
from Crypto.PublicKey import RSA
from binascii import hexlify
from security.otp import *
import os
import sys


class Client:

    def __init__(self, username, encryption_func, gateway_address):
        self.ADDRESS, self.PORT = gateway_address.split(":")
        self.PORT = int(self.PORT)
        self.password_size = 100
        self.username = username
        self.client_pri_key = None
        self.client_pub_key = None
        self.server_pub_key = None
        # OTP
        self.password_file = "otp.pwd"
        self.otp = OTP(self.password_file)
        # generate keys
        self.encryption_function = encryption_func
        pair = RSA.generate(1024)
        self.client_pub_key = pair.publickey().exportKey()
        self.client_pri_key = pair.exportKey()
        self.symmetric_key = hexlify(os.urandom(int(self.encryption_function.key_size/2)))
        self.show_log = False

        self._exchange_key(self.encryption_function.is_symmetric)

    def deliver(self, url, method, headers, body):
        self._init_header(headers)
        headers["URL"] = url
        body = self._encrypt(body)
        self._request("/forward", method, headers, body)

    def register(self, seed):
        passwords = OTPUtil.generate_passwords(seed, self.password_size)
        self.otp.write_passwords(passwords)
        body = {"name": self.username, "password": passwords[-1]}
        self._request("/register", "GET", {}, json.dumps(body))

    """
    receive and identify command
    """
    def do_command(self, command):
        if command[0] == "register":
            if len(command) != 2:
                print("wrong parameter number")
                raise BaseException("wrong parameter number")
            self.register(command[1])
        elif command[0] == "forward":
            if len(command) != 2:
                print("wrong parameter number")
                raise BaseException("wrong parameter number")
            self.deliver("/echo", "GET", {}, command[1])
        elif command[0] == "put":
            if len(command) != 3:
                print("wrong parameter number")
                raise BaseException("wrong parameter number")
            self.deliver("/put", "GET", {}, json.dumps({"key": command[1], "value": command[2]}))
        elif command[0] == "get":
            if len(command) != 2:
                print("wrong parameter number")
                raise BaseException("wrong parameter number")
            self.deliver("/get", "GET", {}, json.dumps({"key": command[1]}))
        elif command[0] == "show" and len(command) == 2 and command[1] == "log":
            self.show_log = True
        elif command[0] == "show" and len(command) == 2 and command[1] == "password":
            print(self.otp.fetch_password())

    def _init_header(self, headers):
        headers["Authentication"] = self._get_authentication()

    def _get_authentication(self):
        password = self.otp.fetch_password()
        return hash.base64encode(self.username + "-" + password)

    def _request(self, url, method, headers, body):
        conn = HTTPConnection(self.ADDRESS, self.PORT)
        if self.show_log or url == "/key":
            print("send message: ["+method+"]"+url+" "+str(body))
        conn.request(method, url, body + ("\n\0\n" if type(body) is str else b"\n\0\n"), headers)
        response = conn.getresponse()
        conn.close()
        if self._need_auth(url) and response.status == http.HTTPStatus.OK:
            self.otp.remove_password()
        res = json.loads(response.read().decode("ascii"))
        print(res)
        return res

    """
    Send private key to server and receive public key
    """
    def _exchange_key(self, symmetric=False):
        body = {
            "key": self.symmetric_key.decode("ascii") if symmetric else self.client_pri_key.decode("ascii"),
            "mode": "symmetric" if symmetric else "asymmetric"}
        response = self._request("/key", "GET", {}, json.dumps(body))
        if not symmetric:
            self.server_pub_key = response["key"].encode()

    def _encrypt(self, text):
        if self.encryption_function.is_symmetric:
            return self.encryption_function.encrypt(self.symmetric_key, text)
        else:
            return self.encryption_function.encrypt(self.server_pub_key, text)

    def _decrypt(self, text):
        if self.encryption_function.is_symmetric:
            return self.encryption_function.decrypt(self.symmetric_key, text)
        else:
            return self.encryption_function.decrypt(self.client_pri_key, text)

    def _need_auth(self, url):
        if url == "/key":
            return False
        else:
            return True

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) == 1:
        client = Client("username", Cipher.RC2, "35.167.103.96:80")
        client.register("seed")
        client.deliver("/echo", "GET", {"testheader": "blank"}, "hello world 1")
        client.deliver("/put", "GET", {}, json.dumps({"key": "key2", "value": "hello 3"}))
        client.deliver("/get", "GET", {}, json.dumps({"key": "key2"}))
    elif len(argv) != 4:
        print("wrong argument number")
    else:
        algorithm_map = {
            "RC2": Cipher.RC2,
            "DES": Cipher.DES,
            "RSA": Cipher.RSA
        }
        client = Client(argv[1], algorithm_map.get(argv[2]), argv[3])
        while True:
            c = input("> ")
            client.do_command(c.split(" "))


