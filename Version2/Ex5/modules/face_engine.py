import cv2
import threading
import time
import os
import numpy as np
from PIL import Image
from modules.voice import AndroidVoice  # <--- [PHASE 9] Import giọng nói

# --- CLASS CAMERA ĐA LUỒNG ---
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

# --- CLASS AI TỰ HỌC & GIỌNG NÓI ---
class FaceEngine:
    def __init__(self, video_source):
        print(f"[AI] Khoi dong Camera: {video_source}...")
        self.vs = VideoStream(src=video_source).start()
        time.sleep(1.0)
        
        # [PHASE 9] Khởi tạo giọng nói
        self.voice = AndroidVoice()
        self.last_speak_time = 0    # Thời điểm nói lần cuối
        self.speak_cooldown = 5.0   # Robot nghỉ 5 giây mới nói câu tiếp
        self.last_status = "" #Biến nhớ xem lúc nãy vừa gặp ai
        
        # Đường dẫn dữ liệu
        self.base_dir = r"D:\Upgrade project\Version2\Memory"
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.trainer_file = os.path.join(self.base_dir, "trainer", "trainer.yml")
        
        # Tạo thư mục
        if not os.path.exists(self.dataset_dir): os.makedirs(self.dataset_dir)
        if not os.path.dirname(self.trainer_file): os.makedirs(os.path.dirname(self.trainer_file))

        # Khởi tạo AI
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Load não bộ
        self.is_trained = False
        if os.path.exists(self.trainer_file):
            try:
                self.recognizer.read(self.trainer_file)
                self.is_trained = True
                print("[AI] Da load tri nho thanh cong!")
            except:
                print("[AI] File tri nho loi, can hoc lai!")
        else:
            print("[AI] Chua tim thay file trainer.yml!")
        
        # Cấu hình điều khiển
        self.target_width = 640
        self.center_min = 0.4
        self.center_max = 0.6
        
        # Trạng thái học tập
        self.is_learning = False
        self.learning_count = 0
        self.target_count = 0   # [PHASE 8 Fix] Mục tiêu số ảnh cần đạt
        self.learning_id = 1
        self.max_samples = 50   # Số ảnh chụp thêm mỗi lần học

    def start_learning(self, user_id):
        """Kích hoạt chế độ học người mới"""
        self.is_learning = True
        self.learning_id = user_id
        
        # [PHASE 8 Fix] Đếm ảnh cũ để học nối tiếp (không ghi đè)
        path = self.dataset_dir
        existing_files = [f for f in os.listdir(path) if f.startswith(f"User.{user_id}.")]
        self.learning_count = len(existing_files)
        
        # Thiết lập mục tiêu mới = Ảnh cũ + 50 ảnh mới
        self.target_count = self.learning_count + self.max_samples
        
        # [PHASE 9] Thông báo bằng giọng nói
        self.voice.say("Bắt đầu học dữ liệu mới. Vui lòng nhìn vào camera")
        
        print(f"\n[AI] ID: {user_id} | Hien co: {self.learning_count} | Muc tieu: {self.target_count}")

    def train_model(self):
        """Hàm tự động Training lại dữ liệu"""
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
        
        if len(ids) > 0:
            self.recognizer.train(faceSamples, np.array(ids))
            self.recognizer.write(self.trainer_file)
            self.is_trained = True
            print(f"[AI] Da hoc xong {len(np.unique(ids))} khuon mat. San sang!")
            # [PHASE 9] Thông báo học xong
            self.voice.say("Đã học xong. Hệ thống sẵn sàng")
        else:
            print("[AI] Khong tim thay du lieu de hoc.")

    def process_frame(self):
        frame = self.vs.read()
        if frame is None: return None, "S"

        # Resize & Xử lý ảnh (Giữ nguyên)
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
        
        # Biến tạm để xác định trạng thái hiện tại là ai
        current_status = "NOBODY" 

        # --- CHẾ ĐỘ 1: ĐANG HỌC (Giữ nguyên) ---
        if self.is_learning:
            # ... (Code phần học tập giữ nguyên y hệt cũ) ...
            cv2.putText(frame, f"DANG HOC: {self.learning_count}/{self.target_count}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                self.learning_count += 1
                file_name = f"User.{self.learning_id}.{self.learning_count}.jpg"
                cv2.imwrite(os.path.join(self.dataset_dir, file_name), gray[y:y+h, x:x+w])
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
                    conf_str = f"Sai so: {round(confidence)}"
                    
                    if confidence < 85: 
                        name = f"ID {id}"
                        if id == 1: 
                            name = "MASTER"
                            current_status = "MASTER" # <--- Xác nhận là Master
                            color = (0, 255, 0)
                            
                            # Điều khiển
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
                            name = f"USER {id}"
                            current_status = "USER" # <--- Xác nhận là Người quen
                            color = (255, 255, 0)
                            status_text = "NGUOI QUEN"
                    else:
                        name = "NGUOI LA"
                        current_status = "STRANGER" # <--- Xác nhận là Người lạ
                        color = (0, 0, 255)
                        status_text = "CANH BAO AN NINH"
                    
                    cv2.putText(frame, conf_str, (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                except:
                    name = "LOI AI"
            else:
                name = "NGUOI LA"
                status_text = "nhan 'N' de them du lieu"

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, str(name), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            break 

        # --- LOGIC XỬ LÝ GIỌNG NÓI THÔNG MINH (FIX BUG) ---
        # 1. Kiểm tra xem người trước mặt có thay đổi so với lúc nãy không?
        is_person_changed = (current_status != self.last_status)
        
        # 2. Kiểm tra thời gian nghỉ
        is_cooldown_over = (current_time - self.last_speak_time) > self.speak_cooldown

        # 3. QUYẾT ĐỊNH NÓI:
        # - Nếu đổi người -> Nói ngay (bỏ qua cooldown)
        # - Nếu người cũ nhưng đã hết thời gian nghỉ -> Nói nhắc lại
        if (is_person_changed and current_status != "NOBODY") or (is_cooldown_over and current_status != "NOBODY"):
            
            text_to_say = ""
            if current_status == "MASTER":
                text_to_say = "Xin chào chủ nhân"
            elif current_status == "USER":
                text_to_say = "Chào người quen"
            elif current_status == "STRANGER":
                text_to_say = "Cảnh báo. Người lạ xâm nhập"

            if text_to_say:
                self.voice.say(text_to_say)
                self.last_speak_time = current_time # Reset đồng hồ
                self.last_status = current_status   # Ghi nhớ người này

        # Nếu không có ai thì reset trạng thái để lần sau gặp lại vẫn chào
        if current_status == "NOBODY":
            self.last_status = "NOBODY"

        cv2.putText(frame, f"LENH: {status_text}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, "[N]: HOC | [Q]: THOAT", (20, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame, command

    def stop(self):
        self.vs.stop()