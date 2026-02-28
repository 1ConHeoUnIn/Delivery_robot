import cv2
import threading
import time
import os
import numpy as np
from PIL import Image
from modules.voice import AndroidVoice
from modules.ears import RobotEars

# --- CÁC CHẾ ĐỘ ---
MODE_STANDBY = "DUNG_YEN"
MODE_AUTO = "TU_LAI"
MODE_MANUAL = "DIEU_KHIEN"

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
    def read(self): return self.frame
    def stop(self): self.stopped = True; self.stream.release()

class FaceEngine:
    def __init__(self, video_source):
        print(f"[AI] Khoi dong Camera: {video_source}...")
        self.vs = VideoStream(src=video_source).start()
        time.sleep(1.0)
        
        self.voice = AndroidVoice()
        self.ears = RobotEars()
        
        # --- QUẢN LÝ TRẠNG THÁI ---
        self.current_mode = MODE_STANDBY
        self.voice_move_cmd = "S"
        self.last_status = "NOBODY"
        
        # [MỚI] Biến "Niềm tin" (Trust) để duy trì quyền điều khiển
        self.last_seen_master_time = 0 
        self.trust_duration = 5.0 # Cho phép điều khiển trong 5 giây sau khi mất dấu Master
        
        # [MỚI] Bộ lọc nhiễu 12 tiếng (Debounce) chống chào liên tục
        self.potential_status = "NOBODY"
        self.status_counter = 0
        self.REQUIRED_STABLE_FRAMES = 10 # Nhìn chằm chằm 10 frame (nửa giây) mới tin
        
        # Biến hệ thống khác
        self.last_speak_time = 0    
        self.last_capture_time = 0
        self.capture_delay = 0.4
        self.base_dir = r"D:\Upgrade project\Version2\Memory"
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.trainer_file = os.path.join(self.base_dir, "trainer", "trainer.yml")
        
        if not os.path.exists(self.dataset_dir): os.makedirs(self.dataset_dir)
        if not os.path.dirname(self.trainer_file): os.makedirs(os.path.dirname(self.trainer_file))
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.is_trained = False
        if os.path.exists(self.trainer_file):
            try: self.recognizer.read(self.trainer_file); self.is_trained = True; print("[AI] Da load tri nho!")
            except: pass
        
        self.target_width = 640
        self.center_min = 0.4
        self.center_max = 0.6
        self.is_learning = False
        self.learning_count = 0
        self.target_count = 0
        self.learning_id = 1
        self.max_samples = 50

        # Khởi động luồng nghe
        self.listening = True
        threading.Thread(target=self.listen_thread, daemon=True).start()
        
        self.voice.say("Xin chào. Tôi đang lắng nghe")

    # --- LUỒNG NGHE (Đã rút gọn) ---
    def listen_thread(self):
        while self.listening:
            text = self.ears.listen()
            if not text: continue
            
            # Chỉ xử lý 2 lệnh cơ bản, mấy lệnh kia tao block hết rồi
            if any(w in text for w in ["đứng yên", "dừng lại", "nghỉ", "stop"]):
                self.current_mode = MODE_STANDBY
                self.voice_move_cmd = "S"
                self.voice.say("Đã dừng")
            
            elif any(w in text for w in ["đi theo", "bám theo", "follow"]):
                self.current_mode = MODE_AUTO
                self.voice.say("Tự động bám theo")
            
            ''' 
            [TẠM ẨN CÁC LỆNH ĐIỀU KHIỂN TAY CHO ĐẾN KHI CÓ XE LĂN BÁNH THỰC TẾ]
            elif any(w in text for w in ["giọng nói", "lắng nghe", "nghe lệnh", "manual"]):
                self.current_mode = MODE_MANUAL
                self.voice_move_cmd = "S"
                self.voice.say("Chế độ giọng nói")

            elif self.current_mode == MODE_MANUAL:
                cmd_updated = False
                if any(w in text for w in ["tiến lên", "lên", "thẳng", "tới"]): 
                    self.voice_move_cmd = "W"; cmd_updated = True
                elif any(w in text for w in ["lùi xuống", "xuống", "sau"]): 
                    self.voice_move_cmd = "B"; cmd_updated = True
                elif any(w in text for w in ["quay trái", "sang trái"]): 
                    self.voice_move_cmd = "L"; cmd_updated = True
                elif any(w in text for w in ["quay phải", "sang phải"]): 
                    self.voice_move_cmd = "R"; cmd_updated = True
                elif any(w in text for w in ["dừng", "thôi"]): 
                    self.voice_move_cmd = "S"; cmd_updated = True
                
                if cmd_updated and self.voice_move_cmd != "S": 
                    print(f"--> [LENH MOI]: {self.voice_move_cmd}") # Debug
            '''

    # --- XỬ LÝ HÌNH ẢNH ---
    def process_frame(self):
        frame = self.vs.read()
        if frame is None: return None, "S"

        height, width = frame.shape[:2]
        ratio = self.target_width / float(width)
        frame = cv2.resize(frame, (self.target_width, int(height * ratio)))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)

        command = "S"
        status_text = "..."
        color = (0, 0, 255)
        current_time = time.time()
        
        detected_status = "NOBODY"
        name_display = "" 

        for (x, y, w, h) in faces:
            if self.is_trained:
                try:
                    id, confidence = self.recognizer.predict(gray[y:y+h, x:x+w])
                    if confidence < 85:
                        if id == 1: 
                            detected_status = "MASTER"
                            name_display = "MASTER"
                            self.last_seen_master_time = current_time # Nạp đầy niềm tin
                            color = (0, 255, 0)
                        else: 
                            detected_status = "USER"
                            name_display = f"USER {id}"
                            color = (255, 255, 0)
                    else:
                        detected_status = "STRANGER"
                        name_display = "NGUOI LA"
                        color = (0, 0, 255)
                    cv2.putText(frame, str(round(confidence)), (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                except: pass
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, name_display, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            break 

        # --- LOGIC ĐIỀU KHIỂN ---
        if self.current_mode == MODE_STANDBY:
            command = "S"
            status_text = "CHE DO: DUNG YEN"
            color = (100, 100, 100)

        elif self.current_mode == MODE_AUTO:
            status_text = "CHE DO: BAM THEO MASTER"
            if detected_status == "MASTER":
                center_x = (x + w/2) / self.target_width
                if center_x < self.center_min: command = "L"
                elif center_x > self.center_max: command = "R"
                else: command = "W"
            else:
                command = "S"
        
        elif self.current_mode == MODE_MANUAL:
            command = self.voice_move_cmd
            status_text = f"VOICE CMD: {self.voice_move_cmd} (Blind Mode)"
            color = (255, 0, 255)

        # --- LOGIC GIAO TIẾP (ĐÃ ÁP DỤNG BỘ LỌC DEBOUNCE 12 TIẾNG) ---
        if detected_status != "NOBODY":
            # Bắt đầu đếm frame xem có ổn định không
            if detected_status == self.potential_status:
                self.status_counter += 1
            else:
                self.potential_status = detected_status
                self.status_counter = 0
            
            # Chỉ khi nào trạng thái giữ nguyên quá 10 frame mới xử lý
            if self.status_counter > self.REQUIRED_STABLE_FRAMES:
                real_status = self.potential_status
                
                if real_status != self.last_status:
                    self.speak_status(real_status)
                    self.last_status = real_status
                    self.last_speak_time = current_time
                else:
                    # Đúng 12 tiếng (43200s) với người quen mới chào lại, người lạ thì 10s
                    limit = 10.0 if real_status == "STRANGER" else 43200.0
                    if (current_time - self.last_speak_time) > limit:
                        self.speak_status(real_status)
                        self.last_speak_time = current_time

        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame, command

    def speak_status(self, status):
        if self.voice.is_busy(): return
        if status == "MASTER": self.voice.say("Xin chào heo")
        elif status == "STRANGER": self.voice.say("người lạ")
        elif status == "USER": self.voice.say("Chào người quen")

    def start_learning(self, user_id): pass 
    def train_model(self): pass 
    def stop(self): self.listening = False; self.vs.stop()