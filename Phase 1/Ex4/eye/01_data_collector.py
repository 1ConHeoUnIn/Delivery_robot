import cv2
import os
import time

# --- CẤU HÌNH ---
DATASET_DIR = r"D:\Upgrade project\Memory\dataset"
# URL Video từ điện thoại của bạn (lấy từ dữ liệu bạn cung cấp)
VIDEO_SOURCE = "http://192.168.2.18:8080/video" 

# Tải bộ phát hiện khuôn mặt
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("--- KHOI TAO THU THAP DU LIEU ---")
face_id = input("Nhap ID khuon mat (VD: 1): ")

print("\n[BAT DAU] Hay nhin vao man hinh camera...")

cap = cv2.VideoCapture(VIDEO_SOURCE)

count = 0
last_save_time = 0      # Thời điểm chụp bức ảnh gần nhất
capture_delay = 0.4     # Chụp mỗi 0.4 giây (để bạn kịp xoay mặt)

# Resize ảnh cho nhẹ và nhanh hơn (Giảm lag)
TARGET_WIDTH = 800 

while True:
    ret, frame = cap.read()
    if not ret:
        print("Loi Camera! Đang thử kết nối lại...")
        continue

    # 1. Resize ảnh để xử lý nhanh hơn (Fix lag video)
    height, width = frame.shape[:2]
    ratio = TARGET_WIDTH / float(width)
    new_height = int(height * ratio)
    frame = cv2.resize(frame, (TARGET_WIDTH, new_height))

    frame = cv2.flip(frame, 1) # Lật ảnh gương
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    # --- XÁC ĐỊNH GIAI ĐOẠN (Logic hướng dẫn) ---
    instruction = ""
    color_text = (0, 255, 0) # Xanh lá

    if count < 20:
        instruction = "1. Nhin THANG (Look Straight)"
        color_text = (0, 255, 0) 
    elif count < 40:
        instruction = "2. Quay nhe TRAI / PHAI"
        color_text = (0, 255, 255) # Vàng
    elif count < 60:
        instruction = "3. Nguoc LEN / Cui XUONG"
        color_text = (255, 0, 255) # Tím
    elif count < 80:
        instruction = "4. Cuoi / Nhan mat (Bieu cam)"
        color_text = (100, 100, 255) # Đỏ nhạt
    else:
        instruction = "5. Sat lai GAN / Ra XA"
        color_text = (0, 165, 255) # Cam

    # --- VẼ GIAO DIỆN (LUÔN HIỆN) ---
    # Vẽ một hình chữ nhật đen ở trên cùng để làm nền cho chữ
    cv2.rectangle(frame, (0, 0), (TARGET_WIDTH, 80), (0, 0, 0), -1)
    
    # Viết chữ lên trên nền đen
    cv2.putText(frame, f"TIEN DO: {count}/100", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, instruction, (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_text, 2)

    # --- XỬ LÝ KHUÔN MẶT ---
    for (x, y, w, h) in faces:
        # Vẽ khung quanh mặt
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Kiểm tra thời gian: Nếu đã qua 0.4s kể từ lần chụp trước thì mới chụp tiếp
        current_time = time.time()
        if current_time - last_save_time > capture_delay:
            count += 1
            
            # Lưu ảnh
            file_name = f"User.{face_id}.{count}.jpg"
            file_path = os.path.join(DATASET_DIR, file_name)
            cv2.imwrite(file_path, gray[y:y+h, x:x+w])
            
            print(f"Da luu anh thu: {count} - {instruction}")
            
            # Cập nhật thời gian chụp
            last_save_time = current_time
            
            # Hiệu ứng nháy xanh khi chụp được
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)

    cv2.imshow('Data Collector (Fix Lag)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    elif count >= 100:
        print("\n[THANH CONG] Da thu thap du 100 mau!")
        break

cap.release()
cv2.destroyAllWindows()