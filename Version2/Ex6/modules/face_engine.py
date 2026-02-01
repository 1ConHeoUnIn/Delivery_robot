import cv2
import threading
import time
import os
import numpy as np
from PIL import Image
from modules.voice import AndroidVoice

# --- CLASS CAMERA ---
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

# --- CLASS AI ---
class FaceEngine:
    def __init__(self, video_source):
        print(f"[AI] Khoi dong Camera: {video_source}...")
        self.vs = VideoStream(src=video_source).start()
        time.sleep(1.0)
        
        # Giọng nói
        self.voice = AndroidVoice()
        
        # [FIX 1] Biến quản lý thời gian nói
        self.last_speak_time = 0    
        self.last_status = "NOBODY" # Lưu người cuối cùng gặp
        
        # [FIX 2] Tốc độ học (Chụp chậm lại)
        self.last_capture_time = 0
        self.capture_delay = 0.4    # Chụp 1 ảnh mỗi 0.4 giây

        # Cấu hình thư mục
        self.base_dir = r"D:\Upgrade project\Version2\Memory"
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.trainer_file = os.path.join(self.base_dir, "trainer", "trainer.yml")
        
        if not os.path.exists(self.dataset_dir): os.makedirs(self.dataset_dir)
        if not os.path.dirname(self.trainer_file): os.makedirs(os.path.dirname(self.trainer_file))

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        self.is_trained = False
        if os.path.exists(self.trainer_file):
            try:
                self.recognizer.read(self.trainer_file)
                self.is_trained = True
                print("[AI] Da load tri nho!")
            except: pass
        else: print("[AI] Chua co tri nho!")

        self.target_width = 640
        self.center_min = 0.4
        self.center_max = 0.6
        
        # Biến học tập
        self.is_learning = False
        self.learning_count = 0
        self.target_count = 0
        self.learning_id = 1
        self.max_samples = 50

    def start_learning(self, user_id):
        self.is_learning = True
        self.learning_id = user_id
        path = self.dataset_dir
        existing = [f for f in os.listdir(path) if f.startswith(f"User.{user_id}.")]
        self.learning_count = len(existing)
        self.target_count = self.learning_count + self.max_samples
        
        # Reset thời gian để bắt đầu chụp
        self.last_capture_time = time.time()
        
        self.voice.say("Bắt đầu học dữ liệu mới")
        print(f"\n[AI] Hoc ID: {user_id}. Muc tieu: {self.target_count}")

    def train_model(self):
        print("[AI] Training...")
        path = self.dataset_dir
        imagePaths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith("jpg")]
        faceSamples, ids = [], []
        
        for imagePath in imagePaths:
            try:
                PIL_img = Image.open(imagePath).convert('L')
                img_numpy = np.array(PIL_img, 'uint8')
                id = int(os.path.split(imagePath)[-1].split(".")[1])
                faces = self.face_cascade.detectMultiScale(img_numpy)
                for (x, y, w, h) in faces:
                    faceSamples.append(img_numpy[y:y+h, x:x+w])
                    ids.append(id)
            except: pass
        
        if len(ids) > 0:
            self.recognizer.train(faceSamples, np.array(ids))
            self.recognizer.write(self.trainer_file)
            self.is_trained = True
            print("[AI] Training Done!")
            self.voice.say("Đã học xong")
        else: print("[AI] Khong co du lieu.")

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
        current_time = time.time()
        
        # Mặc định là NOBODY, nhưng khoan hãy reset last_status vội!
        current_status = "NOBODY"

        # --- CHẾ ĐỘ 1: ĐANG HỌC ---
        if self.is_learning:
            cv2.putText(frame, f"HOC: {self.learning_count}/{self.target_count}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                
                # [FIX 2] Chỉ chụp nếu đã qua 0.4 giây
                if (current_time - self.last_capture_time) > self.capture_delay:
                    self.learning_count += 1
                    file_name = f"User.{self.learning_id}.{self.learning_count}.jpg"
                    cv2.imwrite(os.path.join(self.dataset_dir, file_name), gray[y:y+h, x:x+w])
                    
                    self.last_capture_time = current_time 
                    
                    if self.learning_count >= self.target_count:
                        self.is_learning = False
                        cv2.putText(frame, "TRAINING...", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        cv2.imshow("ROBOT AI VISION", frame)
                        cv2.waitKey(500)
                        self.train_model()
            
            return frame, "S"

        # --- CHẾ ĐỘ 2: NHẬN DIỆN ---
        for (x, y, w, h) in faces:
            if self.is_trained:
                try:
                    id, confidence = self.recognizer.predict(gray[y:y+h, x:x+w])
                    conf_str = f"Diff: {round(confidence)}"
                    
                    if confidence < 85: 
                        name = f"ID {id}"
                        if id == 1: 
                            name = "MASTER"
                            current_status = "MASTER"
                            color = (0, 255, 0)
                            # Điều khiển
                            center_x = (x + w/2) / self.target_width
                            if center_x < self.center_min: command = "L"
                            elif center_x > self.center_max: command = "R"
                            else: command = "W"
                        else:
                            name = f"USER {id}"
                            current_status = "USER"
                            color = (255, 255, 0)
                    else:
                        name = "NGUOI LA"
                        current_status = "STRANGER"
                        color = (0, 0, 255)
                        status_text = "CANH BAO"
                    
                    cv2.putText(frame, conf_str, (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                except: name = "LOI"
            else:
                name = "CHUA HOC"
                status_text = "BAM 'N'"

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, str(name), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            break 

        # --- LOGIC NÓI THÔNG MINH (SỬA LỖI RESET) ---
        
        # Nếu không có ai -> Bỏ qua, KHÔNG reset trạng thái cũ
        # Để khi Master quay lại, robot vẫn nhớ "À, người cuối cùng mình gặp là Master"
        if current_status == "NOBODY":
            pass 
            
        else:
            # 1. Nếu gặp người KHÁC với người lần cuối mình chào
            # (Ví dụ: Lần cuối chào Master, giờ gặp Người lạ -> Báo ngay)
            if current_status != self.last_status:
                self.speak_status(current_status)
                self.last_status = current_status # Cập nhật người mới
                self.last_speak_time = current_time # Reset đồng hồ
            
            # 2. Nếu gặp LẠI người cũ (Vẫn là Master)
            else:
                # Kiểm tra thời gian nghỉ tùy đối tượng
                if current_status == "STRANGER":
                    limit_time = 10.0 # Người lạ thì nhắc lại sau 10s
                else:
                    limit_time = 43200.0 # Master/User thì 12 tiếng mới chào lại
                
                # Nếu đã hết thời gian chờ -> Nói lại
                if (current_time - self.last_speak_time) > limit_time:
                    self.speak_status(current_status)
                    self.last_speak_time = current_time

        cv2.putText(frame, f"LENH: {status_text}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        return frame, command

    def speak_status(self, status):
        """Chọn câu nói và kiểm tra loa bận"""
        if self.voice.is_busy(): return # Loa bận thì thôi

        text = ""
        if status == "MASTER": text = "Xin chào heo"
        elif status == "STRANGER": text = " Người lạ"
        elif status == "USER": text = "Chào người quen"
        
        if text: self.voice.say(text)

    def stop(self):
        self.vs.stop()