import base64


def base64encode(s):
    return base64.b64encode(s.encode()).decode()


def base64decode(s):
    return base64.b64decode(s).decode()

