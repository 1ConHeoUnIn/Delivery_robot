import cv2
import numpy as np
import socket
import os
import threading
import time

# --- CẤU HÌNH ---
ESP32_IP = "192.168.2.28"  # <--- KIỂM TRA LẠI IP CỦA ESP32
ESP32_PORT = 4210
VIDEO_SOURCE = "http://192.168.2.18:8080/video"
TARGET_WIDTH = 640 # Giảm xuống 640 để AI chạy nhanh hơn (Fix lag)

# --- CLASS XỬ LÝ ĐA LUỒNG (QUAN TRỌNG ĐỂ FIX DELAY) ---
class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        # Bắt đầu luồng chạy ngầm
        threading.Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # Liên tục đọc frame mới nhất, frame cũ sẽ bị ghi đè
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# --- KHỞI TẠO KẾT NỐI & AI ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

path = r"D:\Upgrade project\Memory"
trainer_file = os.path.join(path, "trainer", "trainer.yml")

# Tải bộ não
recognizer = cv2.face.LBPHFaceRecognizer_create()
if not os.path.exists(trainer_file):
    print("[LOI] Chua co file trainer.yml! Hay chay file 02_face_training.py truoc.")
    exit()
    
recognizer.read(trainer_file)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# ID 0: None, ID 1: Master
names = ['None', 'MASTER (YOU)', 'User 2', 'User 3']

print(f"--- KET NOI ESP32: {ESP32_IP} ---")
print("[INFO] Dang khoi dong Camera da luong...")

# Bắt đầu luồng camera
vs = VideoStream(src=VIDEO_SOURCE).start()
time.sleep(2.0) # Đợi 2s cho camera ổn định

# Vùng điều khiển (Deadzone)
CENTER_MIN = 0.4
CENTER_MAX = 0.6

# Biến lưu trạng thái gửi lệnh (để tránh spam lệnh giống nhau liên tục)
last_command = ""

while True:
    # Lấy frame mới nhất từ luồng riêng (không bị delay nữa)
    frame = vs.read()
    if frame is None:
        print("Mat tin hieu Camera!")
        break

    # Resize nhẹ gánh cho CPU
    height, width = frame.shape[:2]
    ratio = TARGET_WIDTH / float(width)
    new_height = int(height * ratio)
    frame = cv2.resize(frame, (TARGET_WIDTH, new_height))
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Phát hiện khuôn mặt
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    current_command = "S" # Mặc định dừng
    status_text = "DUNG"
    color_box = (0, 0, 255) # Đỏ (Người lạ)

    found_master = False

    for(x, y, w, h) in faces:
        # AI Phán đoán
        id, confidence = recognizer.predict(gray[y:y+h, x:x+w])

        # Confidence càng THẤP thì càng GIỐNG (0 là giống y hệt)
        if (confidence < 100):
            name = names[id]
            confidence_text = f"{round(100 - confidence)}%"
            
            # --- LOGIC MASTER ---
            if id == 1:
                found_master = True
                color_box = (0, 255, 0) # Xanh lá
                
                # Tính toán vị trí
                center_x = (x + w/2) / TARGET_WIDTH
                
                if center_x < CENTER_MIN:
                    current_command = "L"
                    status_text = "<< RE TRAI"
                elif center_x > CENTER_MAX:
                    current_command = "R"
                    status_text = "RE PHAI >>"
                else:
                    current_command = "W" # Ở giữa -> Đi thẳng (hoặc S nếu muốn đứng yên)
                    status_text = "^ DI THANG"
            else:
                status_text = "KHONG PHAI MASTER"
        else:
            name = "Nguoi la"
            confidence_text = f"{round(100 - confidence)}%"

        # Vẽ giao diện
        cv2.rectangle(frame, (x, y), (x+w, y+h), color_box, 2)
        cv2.putText(frame, str(name), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, str(confidence_text), (x+5, y+h-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

    # --- GỬI LỆNH XUỐNG ESP32 ---
    # Chỉ gửi khi lệnh thay đổi để giảm tải mạng
    if not found_master:
        current_command = "S" # Không thấy Master thì dừng ngay lập tức
        status_text = "TIM KIEM..."

    if current_command != last_command:
        try:
            sock.sendto(current_command.encode(), (ESP32_IP, ESP32_PORT))
            print(f"Gui lenh: {current_command}")
            last_command = current_command
        except Exception as e:
            print(f"Loi mang: {e}")

    # Hiển thị HUD
    cv2.rectangle(frame, (0,0), (TARGET_WIDTH, 40), (0,0,0), -1)
    cv2.putText(frame, f"TRANG THAI: {status_text}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow('Robot AI Control (No Lag)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Dọn dẹp
print("Dang tat he thong...")
vs.stop()
cv2.destroyAllWindows()
sock.close()