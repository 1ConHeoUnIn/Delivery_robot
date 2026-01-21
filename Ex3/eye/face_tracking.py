import cv2
import mediapipe as mp
import socket

# --- CẤU HÌNH KẾT NỐI (Dùng IP ESP32 của bạn) ---
ESP32_IP = "192.168.2.59"  # <--- Nhớ đổi IP đúng
ESP32_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- CẤU HÌNH CAMERA & AI ---
# Số 0 là webcam máy tính, hoặc điền URL của IP Webcam
# URL video thường có đuôi /video. Ví dụ: http://192.168.1.5:8080/video
video_source = "http://192.168.2.18:8080/video" 
cap = cv2.VideoCapture(video_source)

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Ngưỡng Deadzone
CENTER_MIN = 0.4
CENTER_MAX = 0.6

# --- CẤU HÌNH KÍCH THƯỚC CỬA SỔ ---
# Chúng ta sẽ thu nhỏ ảnh lại kích thước này cho dễ nhìn và nhẹ máy
TARGET_WIDTH = 800 

print("Đang khởi động Camera...")

with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Không đọc được camera. Đang thử kết nối lại...")
            # Nếu mất kết nối, thử đợi xíu (tránh spam lỗi liên tục làm treo máy)
            if cv2.waitKey(100) & 0xFF == ord('q'): break
            continue

        # --- BƯỚC 1: RESIZE ẢNH (QUAN TRỌNG) ---
        # Tính toán tỉ lệ để resize mà không bị méo ảnh
        (h, w) = image.shape[:2]
        ratio = TARGET_WIDTH / float(w)
        dim = (TARGET_WIDTH, int(h * ratio))
        
        # Thực hiện resize ảnh nhỏ lại trước khi xử lý (giúp AI chạy nhanh hơn)
        image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # --- BƯỚC 2: XỬ LÝ AI ---
        # Lật ảnh cho giống gương
        image = cv2.flip(image, 1) 
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Xử lý tìm mặt
        results = face_detection.process(image_rgb)

        # Cập nhật lại kích thước sau khi resize (để tính toán vẽ)
        h, w, c = image.shape
        
        command = "S" # Mặc định là Stop
        status = "--- O GIUA ---"

        if results.detections:
            for detection in results.detections:
                # Vẽ khung vuông
                mp_drawing.draw_detection(image, detection)
                
                # Lấy tọa độ bounding box
                bboxC = detection.location_data.relative_bounding_box
                
                # Tính tâm mặt (giá trị từ 0.0 đến 1.0)
                center_x = bboxC.xmin + (bboxC.width / 2)
                
                # --- LOGIC ĐIỀU KHIỂN ---
                if center_x < CENTER_MIN:
                    command = "L"
                    status = "QUAY TRAI <<<<"
                elif center_x > CENTER_MAX:
                    command = "R"
                    status = ">>>> QUAY PHAI"
                else:
                    command = "S"
                    status = "--- O GIUA ---"
                
                # Gửi lệnh sang ESP32
                try:
                    sock.sendto(command.encode(), (ESP32_IP, ESP32_PORT))
                    print(f"Gui: {command} | Tam mat: {center_x:.2f}")
                except Exception as e:
                    print(f"Lỗi gửi UDP: {e}")

                # Chỉ lấy khuôn mặt đầu tiên
                break 
        else:
            # Nếu không thấy mặt -> Gửi lệnh DỪNG cho an toàn
            # (Bạn có thể bỏ dòng này nếu muốn nó giữ nguyên trạng thái cũ)
            sock.sendto(b"S", (ESP32_IP, ESP32_PORT))

        # Hiển thị trạng thái lên màn hình (vẽ sau cùng để chữ đè lên mọi thứ)
        cv2.putText(image, status, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(image, "Nhan 'Q' de thoat", (30, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

        cv2.imshow('Face Tracking AI', image)
        
        # Nhấn phím 'q' để thoát
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
sock.close()