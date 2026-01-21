import socket

# --- NHẬP IP HIỆN TẠI CỦA ESP32 VÀO ĐÂY ---
TARGET_IP = "192.168.2.59"  # <--- SỬA LẠI SỐ NÀY CHO ĐÚNG SERIAL MONITOR
TARGET_PORT = 4210

print(f"Đang chuẩn bị bắn tín hiệu tới: {TARGET_IP}")

# 1. Tìm địa chỉ IP của máy tính (Local IP)
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Không cần kết nối thật, chỉ cần 'giả vờ' để xem OS chọn đường nào
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

local_ip = get_local_ip()
print(f"Máy tính đang dùng IP: {local_ip}")
print("Nếu IP máy tính khác dải 192.168.2.x thì là đang khác mạng với Robot!")

# 2. Tạo socket và ÉP nó gắn vào IP này
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((local_ip, 0)) # <--- Dòng này quan trọng, ép dùng đúng mạng

while True:
    input("Nhấn Enter để gửi lệnh 'W'...")
    sock.sendto(b"W", (TARGET_IP, TARGET_PORT))
    print("-> Đã gửi lệnh W")