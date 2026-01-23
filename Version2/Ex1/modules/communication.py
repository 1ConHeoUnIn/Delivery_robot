import socket

class RobotWiFi:
    def __init__(self, ip, port=4210):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"[KET NOI] Da thiet lap muc tieu toi: {self.ip}:{self.port}")

    def send_command(self, command):
        """Gửi lệnh xuống Robot (W, S, L, R, B)"""
        if self.ip:
            try:
                self.sock.sendto(command.encode(), (self.ip, self.port))
            except Exception as e:
                print(f"[LOI] Khong gui duoc: {e}")

    def close(self):
        self.send_command("S")
        self.sock.close()