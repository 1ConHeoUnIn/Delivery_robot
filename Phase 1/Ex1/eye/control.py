import socket

# --- CẤU HÌNH ---
# Thay số này bằng IP mà ESP32 vừa in ra ở Serial Monitor
ESP32_IP = "192.168.2.59"  
ESP32_PORT = 4210

print(f"Đang nhắm tới ESP32 tại {ESP32_IP}:{ESP32_PORT}")
print("Gõ 'ON' để bật đèn, 'OFF' để tắt đèn, hoặc bất cứ thứ gì để gửi đi.")
print("Gõ 'exit' để thoát.")

# Tạo socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    try:
        # Nhập lệnh từ bàn phím
        message = input("Nhập lệnh >> ")
        
        if message.lower() == "exit":
            break
            
        # Gửi dữ liệu đi (cần encode sang bytes)
        sock.sendto(message.encode(), (ESP32_IP, ESP32_PORT))
        
    except KeyboardInterrupt:
        break

print("Đã ngắt kết nối.")
sock.close()