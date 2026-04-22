import cv2
import threading
import time
import os
import numpy as np
import mediapipe as mp
from PIL import Image
from modules.voice import AndroidVoice
from modules.ears import RobotEars
from ultralytics import YOLO

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
        
        self.last_seen_master_time = 0
        self.trust_duration = 5.0 

        self.potential_status = "NOBODY"
        self.status_counter = 0
        self.REQUIRED_STABLE_FRAMES = 10 

        self.last_speak_time = 0
        self.target_width = 640
        self.center_min = 0.4
        self.center_max = 0.6

        # --- BỘ ĐỆM SANG SỐ (CHỐNG GIẬT) ---
        self.last_sent_cmd = "S"
        self.is_transitioning = False
        self.transition_start_time = 0
        self.transition_delay = 0.5 # Nghỉ 0.5 giây khi đảo chiều gắt (có thể tăng giảm tùy m)

        # --- BỘ NÃO YOLOv8 ---
        print("[AI] Dang tai mo hinh YOLOv8n...")
        self.model = YOLO("yolov8n.pt") 

        # --- BỘ NÃO MEDIAPIPE (BẮT BÀN TAY) ---
        print("[AI] Dang tai mo hinh MediaPipe Hands...")
        self.mp_hands = mp.solutions.hands
        # Chỉ cho phép bắt tối đa 1 bàn tay để tiết kiệm CPU hết mức
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=1, 
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # --- ĐỒ NGHỀ HỌC KHUÔN MẶT ---
        self.base_dir = r"D:\Upgrade project\Version2\Memory"
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.trainer_file = os.path.join(self.base_dir, "trainer", "trainer.yml")

        if not os.path.exists(self.dataset_dir): os.makedirs(self.dataset_dir)
        if not os.path.exists(os.path.dirname(self.trainer_file)): os.makedirs(os.path.dirname(self.trainer_file))

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.is_trained = False
        
        if os.path.exists(self.trainer_file):
            try: 
                self.recognizer.read(self.trainer_file)
                self.is_trained = True
                print("[AI] Da load tri nho khuon mat!")
            except Exception as e:
                print(f"[LOI] Khong doc duoc file trainer: {e}")

        self.is_learning = False
        self.learning_count = 0
        self.learning_id = 1
        self.max_samples = 50
        
        # Khởi tạo biến nhớ tạm Tracker
        self.master_track_id = -1 

        # Khởi động luồng nghe
        self.listening = True
        threading.Thread(target=self.listen_thread, daemon=True).start()
        self.voice.say("Xin chào. Tôi đang lắng nghe")

    def listen_thread(self):
        while self.listening:
            text = self.ears.listen()
            if not text: continue
            if any(w in text for w in ["đứng yên", "dừng lại", "nghỉ", "stop"]):
                self.current_mode = MODE_STANDBY
                self.voice_move_cmd = "S"
                self.voice.say("Đã dừng")
            elif any(w in text for w in ["đi theo", "bám theo", "follow"]):
                self.current_mode = MODE_AUTO
                self.voice.say("Tự động bám theo")

    def process_frame(self):
        frame = self.vs.read()
        if frame is None: return None, "S"
        
        height, width = frame.shape[:2]
        ratio = self.target_width / float(width)
        frame = cv2.resize(frame, (self.target_width, int(height * ratio)))
        
        command = "S"
        status_text = "..."
        color = (0, 0, 255)
        current_time = time.time()

        detected_status = "NOBODY"
        name_display = ""
        
        # --- BẬT TRACKER CỦA YOLOv8 (BỘ NHỚ TẠM) ---
        results = self.model.track(frame, classes=0, persist=True, verbose=False)
        best_box = None
        best_track_id = -1
        max_area = 0
        
        # Quét tìm dáng người và lấy ID theo dõi (Track ID)
        for r in results:
            boxes = r.boxes
            if boxes.id is not None:
                track_ids = boxes.id.int().cpu().tolist()
                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    area = (x2 - x1) * (y2 - y1)
                    if area > max_area:
                        max_area = area
                        best_box = (int(x1), int(y1), int(x2), int(y2))
                        best_track_id = track_id
                    
        if best_box:
            x1, y1, x2, y2 = best_box
            w_box = x2 - x1
            h_box = y2 - y1
            
            detected_status = "STRANGER"
            name_display = f"NGUOI LA (ID: {best_track_id})"
            color = (0, 0, 255) # Đỏ
            
            # --- KIỂM TRA BỘ NHỚ TẠM ---
            if best_track_id != -1 and best_track_id == self.master_track_id:
                detected_status = "MASTER"
                name_display = f"MASTER (TRACK ID: {best_track_id})" 
                color = (0, 255, 255) # Vàng Cyan
                self.last_seen_master_time = current_time 

           # --- TÌM MẶT ĐỂ MỞ KHÓA (GHI NHỚ DÁNG) ---
            head_y2 = y1 + int(h_box / 2) 
            head_roi = frame[max(0, y1):head_y2, max(0, x1):x2] 
            
            # [TỐI ƯU HÓA: BẬT/TẮT AI KHUÔN MẶT]
            # Công tắc thần kỳ: Chỉ tìm mặt khi đang là NGƯỜI LẠ (chưa khóa Track ID) HOẶC lúc mày bấm phím 'n' để học
            if (detected_status != "MASTER" or self.is_learning) and (head_roi.shape[0] > 0 and head_roi.shape[1] > 0):
                gray_roi = cv2.cvtColor(head_roi, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray_roi, 1.2, 5)

                for (fx, fy, fw, fh) in faces:
                    cv2.rectangle(frame, (x1 + fx, y1 + fy), (x1 + fx + fw, y1 + fy + fh), (255, 0, 0), 2)
                    
                    if self.is_learning:
                        self.learning_count += 1
                        file_name = f"User.{self.learning_id}.{self.learning_count}.jpg"
                        cv2.imwrite(os.path.join(self.dataset_dir, file_name), gray_roi[fy:fy+fh, fx:fx+fw])
                        cv2.putText(frame, f"Dang hoc: {self.learning_count}/{self.max_samples}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        
                        if self.learning_count >= self.max_samples:
                            self.is_learning = False
                            threading.Thread(target=self.train_model).start()
                            
                    elif self.is_trained:
                        try:
                            id, confidence = self.recognizer.predict(gray_roi[fy:fy+fh, fx:fx+fw])
                            if confidence < 75:
                                if id == 1:
                                    detected_status = "MASTER"
                                    name_display = f"MASTER (LOCKED ID: {best_track_id})"
                                    color = (0, 255, 0) # Xanh lá
                                    
                                    # CHỐT ĐƠN: Ép bộ nhớ tạm ghi nhớ cái Track ID của dáng người này!
                                    self.master_track_id = best_track_id 
                                    self.last_seen_master_time = current_time
                                else:
                                    detected_status = "USER"
                                    name_display = f"USER {id}"
                                    color = (255, 255, 0)
                            else:
                                detected_status = "STRANGER"
                                name_display = "NGUOI LA"
                                color = (0, 0, 255)
                                
                            cv2.putText(frame, f"Sai so: {round(confidence)}", (x1 + fx, y1 + fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
                        except Exception as e:
                            pass
                    break # Chỉ xét khuôn mặt đầu tiên
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name_display, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Gửi lệnh rẽ
           # --- LOGIC ĐIỀU KHIỂN & NHẪN THUẬT LÙI XE ---
            if self.current_mode == MODE_AUTO:
                if detected_status == "MASTER":
                    center_x = (x1 + w_box/2) / self.target_width
                    
                    # 1. CẮT VÙNG ẢNH CỦA MASTER ĐỂ TÌM BÀN TAY (Giảm tải CPU)
                    master_roi = frame[max(0, y1):y2, max(0, x1):x2]
                    hand_raised = False # Đổi tên biến để phù hợp logic mới
                    
                    if master_roi.shape[0] > 0 and master_roi.shape[1] > 0:
                        roi_rgb = cv2.cvtColor(master_roi, cv2.COLOR_BGR2RGB)
                        hand_results = self.hands.process(roi_rgb)
                        
                        if hand_results.multi_hand_landmarks:
                            for hand_landmarks in hand_results.multi_hand_landmarks:
                                # Vẽ mấy cái chấm màu hồng lên các khớp tay cho ngầu
                                # Vẽ mấy cái chấm màu hồng lên các khớp tay cho ngầu
                                for lm in hand_landmarks.landmark:
                                    h_roi, w_roi, c_roi = master_roi.shape
                                    cx, cy = int(lm.x * w_roi) + x1, int(lm.y * h_roi) + y1
                                    cv2.circle(frame, (cx, cy), 4, (255, 0, 255), cv2.FILLED)
                                
                                # --- FIX LOGIC: TRỤC Y CAMERA BỊ NGƯỢC ---
                                # Cổ tay (điểm 0) phải nằm DƯỚI gốc ngón tay (điểm 9) -> Y của 0 phải LỚN HƠN Y của 9
                                if hand_landmarks.landmark[0].y > hand_landmarks.landmark[9].y:
                                    # Đầu ngón giữa (điểm 12) phải xòe thẳng lên TRÊN gốc ngón tay (điểm 9) -> Y nhỏ hơn
                                    if hand_landmarks.landmark[12].y < hand_landmarks.landmark[9].y:
                                        hand_raised = True

                    
                    # 2. XỬ LÝ LỆNH DI CHUYỂN DỰA TRÊN THỨ TỰ ƯU TIÊN
                    if hand_raised:
                        command = "B" # Gửi lệnh LÙI
                        cv2.putText(frame, "NHAN THUAT - LUI XE!", (x1, y1 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                    else:
                        # Tính độ lệch từ tâm người tới chính giữa khung hình (0.5)
                        error = abs(center_x - 0.5)
                        
                        # --- FIX: Ưu tiên rẽ đầu nhìn Sếp trước (bất kể khoảng cách xa gần) ---
                        if error > 0.1:
                            min_speed = 40  
                            max_speed = 80  
                            speed = int(min_speed + ((error - 0.1) / 0.4) * (max_speed - min_speed))
                            speed = min(max_speed, max(min_speed, speed)) 
                            
                            if center_x < 0.5: 
                                command = f"R{speed}" 
                            else: 
                                command = f"L{speed}" 
                        # --- Đã nhìn thẳng Sếp rồi, giờ mới xét khoảng cách an toàn ---
                        else:
                            if w_box > (self.target_width * 0.6): 
                                command = "S" # Đứng quá gần thì phanh gấp, không tiến lên dẫm chân
                                cv2.putText(frame, "QUA GAN - DUNG!", (x1, y1 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            else:
                                command = "W" # Khoảng cách an toàn, bám theo thôi!
                else:
                    command = "S" # Tránh trường hợp người lạ mà nó vẫn đi theo

        # --- LOGIC ĐIỀU KHIỂN CHUNG ---
        if self.current_mode == MODE_STANDBY:
            command = "S"
            status_text = "CHE DO: DUNG YEN"
            color = (100, 100, 100)
        elif self.current_mode == MODE_AUTO:
            status_text = "CHE DO: BAM THEO NGUOI"
            if detected_status == "NOBODY":
                command = "S"

        # --- LOGIC GIAO TIẾP DEBOUNCE ---
        if detected_status != "NOBODY":
            if detected_status == self.potential_status:
                self.status_counter += 1
            else:
                self.potential_status = detected_status
                self.status_counter = 0

            if self.status_counter > self.REQUIRED_STABLE_FRAMES:
                real_status = self.potential_status
                if real_status != self.last_status:
                    self.speak_status(real_status)
                    self.last_status = real_status
                    self.last_speak_time = current_time
                else:
                    limit = 10.0 if real_status == "STRANGER" else 43200.0
                    if (current_time - self.last_speak_time) > limit:
                        self.speak_status(real_status)
                        self.last_speak_time = current_time

        # --- BỘ LỌC LỆNH CHỐNG GIẬT CẦU H ---
        raw_command = command 
        
        # Chỉ lấy chữ cái đầu tiên (W, B, L, R, S) để check ngược chiều
        cmd_type = raw_command[0] if len(raw_command) > 0 else "S"
        last_cmd_type = self.last_sent_cmd[0] if len(self.last_sent_cmd) > 0 else "S"
        
        opposite_cmds = {"W": "B", "B": "W", "L": "R", "R": "L"}
        
        if self.is_transitioning:
            if (current_time - self.transition_start_time) < self.transition_delay:
                command = "S" 
                cv2.putText(frame, "DANG XA QUAN TINH...", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            else:
                self.is_transitioning = False
                self.last_sent_cmd = raw_command
        else:
            # Check xem có bị bẻ lái gắt không dựa trên chữ cái đầu tiên
            if opposite_cmds.get(last_cmd_type) == cmd_type:
                self.is_transitioning = True
                self.transition_start_time = current_time
                command = "S" 
            else:
                self.last_sent_cmd = raw_command

        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame, command
    
    def speak_status(self, status):
        if self.voice.is_busy(): return
        if status == "MASTER": self.voice.say("Xin chào heo")
        elif status == "STRANGER": self.voice.say("người lạ")
        elif status == "USER": self.voice.say("Chào người quen")

    def start_learning(self, user_id):
        print(f"\n[AI] BAT DAU THU THAP KHUON MAT CHO ID: {user_id}")
        self.learning_id = user_id
        
        # --- FIX: HỌC CỘNG DỒN ---
        existing_files = [f for f in os.listdir(self.dataset_dir) if f.startswith(f"User.{user_id}.")]
        if existing_files:
            counts = [int(f.split('.')[2]) for f in existing_files]
            self.learning_count = max(counts)
            print(f"[AI] Da co {self.learning_count} anh. Se chup tiep...")
        else:
            self.learning_count = 0
            
        self.max_samples = self.learning_count + 50 
        self.is_learning = True
        self.voice.say("Bắt đầu thu thập dữ liệu")

    def train_model(self):
        print("\n[AI] DANG HUAN LUYEN MO HINH. VUI LONG DOI...")
        self.voice.say("Đang huấn luyện mô hình")
        
        image_paths = [os.path.join(self.dataset_dir, f) for f in os.listdir(self.dataset_dir) if f.endswith('.jpg')]
        faces = []
        ids = []
        
        for image_path in image_paths:
            try:
                PIL_img = Image.open(image_path).convert('L')
                img_numpy = np.array(PIL_img, 'uint8')
                id = int(os.path.split(image_path)[-1].split(".")[1])
                faces.append(img_numpy)
                ids.append(id)
            except Exception as e:
                print(f"Loi doc anh: {e}")

        if len(faces) > 0:
            self.recognizer.train(faces, np.array(ids))
            self.recognizer.write(self.trainer_file)
            self.is_trained = True
            print(f"[AI] HUAN LUYEN XONG! Da luu vao {self.trainer_file}")
            self.voice.say("Huấn luyện hoàn tất")
        else:
            print("[AI] Khong co du lieu!")

    def stop(self): self.listening = False; self.vs.stop()