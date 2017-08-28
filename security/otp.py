class OTP:
    def __init__(self, file_path):
        self.file_path=file_path

    def write_passwords(self, passwords):
        f = open(self.file_path, "w+")
        for p in passwords:
            f.write(p+"\r\n")
        f.close()

    def fetch_password(self):
        f = open(self.file_path, "r")
        lines = f.readlines()
        f.close()
        return str.strip(lines[-1], "\r\n")

    def remove_password(self):
        f = open(self.file_path, "r")
        lines = f.readlines()
        f.close()
        f = open(self.file_path, "w")
        for idx, l in enumerate(lines):
            if idx != len(lines)-1:
                f.write(l)
        f.close()
