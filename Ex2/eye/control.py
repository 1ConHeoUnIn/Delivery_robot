import socket

# --- CẤU HÌNH ---
# 1. Nhập IP mà ESP32 vừa in ra màn hình Serial Monitor vào đây
ESP32_IP = "192.168.2.59" 
ESP32_PORT = 4210

print(f"--- KẾT NỐI ĐẾN ROBOT TẠI {ESP32_IP}:{ESP32_PORT} ---")
print("HƯỚNG DẪN ĐIỀU KHIỂN:")
print("  w  : Đi thẳng (Forward)")
print("  b  : Đi lùi (Backward)")
print("  a  : Quay trái (Left)")
print("  d  : Quay phải (Right)")
print("  s  : DỪNG LẠI (Stop)")
print("  q  : Thoát chương trình")
print("-------------------------------------------------------")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    try:
        # Nhập lệnh từ bàn phím
        key = input("Nhập lệnh (w/a/s/d/b) >> ").lower().strip()

        if key == "q":
            break
        
        # Mapping từ phím tắt sang lệnh gửi đi
        command = ""
        if key == "w":
            command = "W"  # Khớp với code main.cpp
        elif key == "b":
            command = "B"
        elif key == "a":
            command = "L"  # Code ESP32 quy định L là Left
        elif key == "d":
            command = "R"  # Code ESP32 quy định R là Right
        elif key == "s":
            command = "S"  # Stop
        else:
            print("Phím không hợp lệ!")
            continue

        # Gửi lệnh sang ESP32
        sock.sendto(command.encode(), (ESP32_IP, ESP32_PORT))
        print(f"-> Đã gửi: {command}")

    except KeyboardInterrupt:
        break

print("Đã ngắt kết nối.")
sock.close()