from data.database import *
from util.otputil import *


class Account:

    TOPIC = "account"

    def __init__(self):
        self.database = Database()

    def _get_password(self, username):
        return self.database.get(Account.TOPIC, username)

    def set_password(self, username, password):
        self.database.append(Account.TOPIC, username, password)

    def validate(self, username, password):
        p = self._get_password(username)
        ret = OTPUtil.validate(password, p)
        return ret
