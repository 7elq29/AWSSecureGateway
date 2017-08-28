from pyblake2 import *


class OTPUtil(object):

    @staticmethod
    def generate_passwords(seed, size):
        h = blake2b()
        h.update(seed.encode())
        passwords = [h.hexdigest()]
        for i in range(1, size):
            h = blake2b()
            h.update(passwords[i - 1].encode())
            passwords.append(h.hexdigest())
        return passwords

    @staticmethod
    def validate(password, true_value):
        h = blake2b()
        h.update(password.encode())
        return h.hexdigest() == true_value

    @staticmethod
    def hash(text):
        h = blake2b()
        h.update(text.encode())
        return h.hexdigest()

