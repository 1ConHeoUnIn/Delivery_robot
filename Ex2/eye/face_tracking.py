import cv2
import mediapipe as mp
import socket

# --- CẤU HÌNH KẾT NỐI (Dùng IP ESP32 của bạn) ---
ESP32_IP = "192.168.2.57"  # <--- Nhớ đổi IP đúng
ESP32_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- CẤU HÌNH CAMERA & AI ---
cap = cv2.VideoCapture("http://192.168.2.18:8080/video") # Số 0 thường là webcam laptop, nếu dùng IP Camera thì điền URL (vd: "http://192.168.1.5:8080/video")

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Ngưỡng để xác định "Ở giữa". 
# Màn hình chia từ 0 đến 1. Tâm là 0.5.
# Khoảng an toàn (Deadzone) là từ 0.4 đến 0.6.  
CENTER_MIN = 0.4
CENTER_MAX = 0.6

print("Đang khởi động Camera...")

with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Không đọc được camera via IP Webcam/USB")
            continue

        # Lật ảnh cho giống gương (nếu cần), và chuyển sang màu RGB để MediaPipe hiểu
        image = cv2.flip(image, 1) 
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Xử lý tìm mặt
        results = face_detection.process(image_rgb)

        # Lấy kích thước khung hình
        h, w, c = image.shape
        
        command = "S" # Mặc định là Stop (Dừng/Ở giữa)

        if results.detections:
            for detection in results.detections:
                # Vẽ khung vuông quanh mặt
                mp_drawing.draw_detection(image, detection)
                
                # Lấy tọa độ khung bao quanh mặt (Bounding Box)
                # bboxC có dạng: [xmin, ymin, width, height] (giá trị từ 0.0 đến 1.0)
                bboxC = detection.location_data.relative_bounding_box
                
                # Tính tâm của khuôn mặt (trục X)
                center_x = bboxC.xmin + (bboxC.width / 2)
                
                # --- LOGIC ĐIỀU KHIỂN ---
                if center_x < CENTER_MIN:
                    command = "L" # Left - Mặt đang ở bên trái -> Robot cần quay trái
                    status = "QUAY TRAI <<<<"
                elif center_x > CENTER_MAX:
                    command = "R" # Right - Mặt đang ở bên phải -> Robot cần quay phải
                    status = ">>>> QUAY PHAI"
                else:
                    command = "S" # Stop - Mặt ở giữa
                    status = "--- O GIUA ---"
                
                # Hiển thị trạng thái lên màn hình
                cv2.putText(image, status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Gửi lệnh sang ESP32
                # Chỉ gửi khi cần thiết để tránh spam mạng (có thể tối ưu sau)
                sock.sendto(command.encode(), (ESP32_IP, ESP32_PORT))
                print(f"Gui lenh: {command} | Tam mat: {center_x:.2f}")

                # Chỉ lấy khuôn mặt đầu tiên để điều khiển cho dễ
                break 

        cv2.imshow('Face Tracking AI', image)
        
        # Nhấn phím 'q' để thoát
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
sock.close()