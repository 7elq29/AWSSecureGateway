#!/usr/bin/env python3.5

from packages.rc2 import *
import pyDes
from Crypto.PublicKey import RSA
import binascii
import os


class Cipher:

    ##
    # RC2
    ##
    class RC2:

        is_symmetric = True
        key_size = 256

        @staticmethod
        def encrypt(key, plaintext):
            rc2_ctx = RC2(key)
            msg = bytearray(plaintext, 'ascii')
            return rc2_ctx.encrypt(msg, MODE_ECB)

        @staticmethod
        def decrypt(key, ciphertext):
            rc2_ctx = RC2(key)
            return rc2_ctx.decrypt(ciphertext, MODE_ECB).strip(b'\n').strip(b'\x00')

    ##
    # DES
    ##
    class DES:

        is_symmetric = True
        key_size = 8

        @staticmethod
        def encrypt(key, plaintext):
            cipher = pyDes.des(key, pyDes.CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
            msg = bytearray(plaintext, 'ascii')
            return cipher.encrypt(msg)

        @staticmethod
        def decrypt(key, cipher_text):
            cipher = pyDes.des(key, pyDes.CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
            return cipher.decrypt(cipher_text, padmode=pyDes.PAD_PKCS5).strip(b'\n').strip(b'\x00')

    ##
    # RSA
    ##
    class RSA:

        is_symmetric = False
        key_size = 1024

        @staticmethod
        def encrypt(key, plaintext):
            cipher = RSA.importKey(key)
            msg = plaintext.encode('ascii')
            return cipher.encrypt(msg, None)[0]

        @staticmethod
        def decrypt(key, cipher_text):
            cipher = RSA.importKey(key)
            return cipher.decrypt(cipher_text).strip(b'\n').strip(b'\x00')


if __name__ == "__main__":
    des = Cipher.RSA
    text = "hello world"
    pair = RSA.generate(1024)
    client_pub_key = pair.publickey().exportKey()
    client_pri_key = pair.exportKey()
    cipher_text = des.encrypt(client_pub_key, text)
    print(des.decrypt(client_pri_key, cipher_text))