import cv2
import threading
import time
import os
import numpy as np
from PIL import Image

# --- CLASS CAMERA ĐA LUỒNG (Giữ nguyên) ---
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
            if self.stopped: return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# --- CLASS AI TỰ HỌC (NÂNG CẤP) ---
class FaceEngine:
    def __init__(self, video_source):
        print(f"[AI] Khoi dong Camera: {video_source}...")
        self.vs = VideoStream(src=video_source).start()
        time.sleep(1.0)
        
        # Đường dẫn dữ liệu
        self.base_dir = r"D:\Upgrade project\Version2\Memory"
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.trainer_file = os.path.join(self.base_dir, "trainer", "trainer.yml")
        
        # Tạo thư mục nếu chưa có
        if not os.path.exists(self.dataset_dir): os.makedirs(self.dataset_dir)
        if not os.path.dirname(self.trainer_file): os.makedirs(os.path.dirname(self.trainer_file))

        # Khởi tạo AI
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Load não bộ (nếu đã có)
        self.names = ['None', 'Master'] # ID 0 là rỗng, ID 1 là Master mặc định
        self.is_trained = False # <--- [MỚI] Mặc định là chưa học
        if os.path.exists(self.trainer_file):
            try:
                self.recognizer.read(self.trainer_file)
                self.is_trained = True  # <--- [MỚI] Đánh dấu là đã có não
                print("[AI] Da load tri nho thanh cong!")
            except:
                print("[AI] Chua co tri nho, can hoc ngay!")
        else:
            print("[AI] Chua tim thay file trainer.yml tai duong dan moi!")
        # Cấu hình điều khiển
        self.target_width = 640
        self.center_min = 0.4
        self.center_max = 0.6
        
        # Trạng thái học tập
        self.is_learning = False
        self.learning_count = 0
        self.learning_id = 1
        self.max_samples = 50 # Số ảnh cần chụp để học
        self.target_count = 50

    def start_learning(self, user_id):
        """Kích hoạt chế độ học người mới"""
        self.is_learning = True
        self.learning_id = user_id
        
        # Đếm ảnh cũ
        path = self.dataset_dir
        existing_files = [f for f in os.listdir(path) if f.startswith(f"User.{user_id}.")]
        self.learning_count = len(existing_files)
        
        # [QUAN TRỌNG] Thiết lập mục tiêu mới = Ảnh cũ + 50 ảnh mới
        self.target_count = self.learning_count + self.max_samples
        
        print(f"\n[AI] ID: {user_id} | Hien co: {self.learning_count} | Muc tieu: {self.target_count}")
        print("Vui long nhin vao Camera...")
    def train_model(self):
        """Hàm tự động Training lại dữ liệu (chạy ngầm)"""
        print("[AI] Dang sap xep lai ky uc (Training)...")
        path = self.dataset_dir
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []

        for imagePath in imagePaths:
            if not imagePath.endswith("jpg"): continue
            PIL_img = Image.open(imagePath).convert('L')
            img_numpy = np.array(PIL_img, 'uint8')
            try:
                id = int(os.path.split(imagePath)[-1].split(".")[1])
                faces = self.face_cascade.detectMultiScale(img_numpy)
                for (x, y, w, h) in faces:
                    faceSamples.append(img_numpy[y:y+h, x:x+w])
                    ids.append(id)
            except: pass
        
        # Training
        if len(ids) > 0:
            self.recognizer.train(faceSamples, np.array(ids))
            self.recognizer.write(self.trainer_file)
            self.is_trained = True  # <--- [MỚI] Học xong thì bật não lên
            print(f"[AI] Da hoc xong {len(np.unique(ids))} khuon mat. San sang!")
        else:
            print("[AI] Khong tim thay du lieu de hoc.")

    def process_frame(self):
        frame = self.vs.read()
        if frame is None: return None, "S"

        # Resize
        height, width = frame.shape[:2]
        ratio = self.target_width / float(width)
        new_height = int(height * ratio)
        frame = cv2.resize(frame, (self.target_width, new_height))
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)

        command = "S"
        status_text = "DUNG"
        color = (0, 0, 255)

        # --- CHẾ ĐỘ 1: ĐANG HỌC (COLLECTING) ---
        if self.is_learning:
            # (Giữ nguyên code phần học tập cũ)
            cv2.putText(frame, f"DANG HOC: {self.learning_count}/{self.max_samples}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                self.learning_count += 1
                file_name = f"User.{self.learning_id}.{self.learning_count}.jpg"
                cv2.imwrite(os.path.join(self.dataset_dir, file_name), gray[y:y+h, x:x+w])
                time.sleep(0.1) 
                if self.learning_count >= self.target_count:
                    self.is_learning = False
                    cv2.putText(frame, "TRAINING...", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.imshow("ROBOT AI VISION", frame)
                    cv2.waitKey(500)
                    self.train_model()
            return frame, "S"

        # --- CHẾ ĐỘ 2: NHẬN DIỆN & ĐIỀU KHIỂN ---
        for (x, y, w, h) in faces:
            if self.is_trained:
                try:
                    # Nhận diện
                    id, confidence = self.recognizer.predict(gray[y:y+h, x:x+w])
                    
                    # [QUAN TRỌNG] Hiển thị điểm sai lệch lên màn hình để Debug
                    # Làm tròn số cho gọn
                    conf_str = f"Sai so: {round(confidence)}"
                    
                    # [LOGIC MỚI] SIẾT CHẶT AN NINH
                    # Nếu sai số < 85 (Rất giống) thì mới nhận
                    if confidence < 85:
                        name = f"ID {id}"
                        if id == 1: 
                            name = "MASTER"
                            color = (0, 255, 0) # Xanh lá
                            
                            # Logic điều khiển
                            center_x = (x + w/2) / self.target_width
                            if center_x < self.center_min:
                                command = "L"
                                status_text = "<< RE TRAI"
                            elif center_x > self.center_max:
                                command = "R"
                                status_text = "RE PHAI >>"
                            else:
                                command = "W"
                                status_text = "^ DI THANG"
                        else:
                            name = f"USER {id}" # Người quen khác (User 2, 3...)
                            color = (255, 255, 0) # Màu vàng
                            status_text = "NGUOI QUEN "
                    
                    else:
                        # Nếu sai số >= 55 -> Quá khác -> Coi là người lạ dù thuật toán đoán là ID mấy
                        name = "NGUOI LA"
                        color = (0, 0, 255) # Đỏ
                        status_text = "????"
                    
                    # Hiển thị độ sai lệch ngay dưới tên
                    cv2.putText(frame, conf_str, (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

                except:
                    name = "LOI AI"
                    status_text = "ERROR"
            
            else:
                name = "NGUOI LA"
                color = (0, 165, 255) 
                status_text = "nhan 'N' de them du lieu"

            # Vẽ khung và tên
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, str(name), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            break 

        cv2.putText(frame, f"LENH: {status_text}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, "[N]: HOC NGUOI MOI | [Q]: THOAT", (20, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame, command

    def stop(self):
        self.vs.stop()