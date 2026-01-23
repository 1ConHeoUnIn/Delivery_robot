import cv2
import threading
import time

# --- CLASS XỬ LÝ CAMERA ĐA LUỒNG (Fix Lag) ---
class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# --- CLASS XỬ LÝ LOGIC AI ---
class FaceEngine:
    def __init__(self, video_source):
        print(f"[AI] Dang khoi dong Camera: {video_source}...")
        self.vs = VideoStream(src=video_source).start()
        time.sleep(2.0) # Đợi camera ổn định
        
        # Tải bộ nhận diện khuôn mặt cơ bản
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        
        # Cấu hình vùng điều khiển (Deadzone)
        self.target_width = 640
        self.center_min = 0.4
        self.center_max = 0.6

    def process_frame(self):
        """
        Hàm này thực hiện: Đọc ảnh -> Tìm mặt -> Tính toán lệnh
        Trả về: (frame_đã_vẽ, lệnh_điều_khiển)
        """
        frame = self.vs.read()
        if frame is None:
            return None, "S"

        # Resize để xử lý nhanh
        height, width = frame.shape[:2]
        ratio = self.target_width / float(width)
        new_height = int(height * ratio)
        frame = cv2.resize(frame, (self.target_width, new_height))
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)

        command = "S" # Mặc định đứng yên
        status_text = "DUNG (TIM KIEM)"
        color = (0, 0, 255) # Đỏ

        # Nếu thấy ít nhất 1 khuôn mặt
        for (x, y, w, h) in faces:
            color = (0, 255, 0) # Xanh lá (Đã thấy)
            
            # Tính tâm khuôn mặt (từ 0.0 đến 1.0)
            center_x = (x + w/2) / self.target_width
            
            # --- LOGIC RA QUYẾT ĐỊNH ---
            if center_x < self.center_min:
                command = "L"
                status_text = "<< RE TRAI"
            elif center_x > self.center_max:
                command = "R"
                status_text = "RE PHAI >>"
            else:
                command = "W" # Ở giữa -> Đi tới
                status_text = "^ DI THANG"
            
            # Vẽ khung
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, "TARGET", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Chỉ lấy mặt to nhất/đầu tiên để xử lý
            break 

        # Vẽ giao diện HUD
        cv2.putText(frame, f"LENH: {status_text}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        
        return frame, command

    def stop(self):
        self.vs.stop()