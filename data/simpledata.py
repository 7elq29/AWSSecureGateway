from data.database import *
from util.otputil import *


class SimpleData:

    TOPIC = "data"

    def __init__(self):
        self.database = Database()

    def get_data(self, key):
        return self.database.get(SimpleData.TOPIC, key)

    def set_data(self, key, value):
        self.database.append(SimpleData.TOPIC, key, value)

