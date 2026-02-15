import speech_recognition as sr

class RobotEars:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        
        print("[TAI] Dang hieu chinh tieng on nen... (Im lang 1 giay)")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # [SỬA] Hạ ngưỡng xuống mức trung bình (400-600 là mức nói chuyện thường)
            # Set mức 600 để lọc tiếng quạt nhẹ, nhưng vẫn nghe được tiếng người
            self.recognizer.energy_threshold = 600
            
            # [MỚI] Cho phép tự điều chỉnh, nhưng rất chậm (để thích nghi môi trường)
            self.recognizer.dynamic_energy_threshold = True 
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5

        print(f"[TAI] San sang. Nguong nghe ban dau: {self.recognizer.energy_threshold}")

    def listen(self):
        try:
            with self.mic as source:
                print("[TAI] Dang lang nghe...")
                # phrase_time_limit=3: Nghe trong 3 giây (đủ cho 1 câu lệnh)
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=2)
            
            # Dịch sang văn bản
            text = self.recognizer.recognize_google(audio, language='vi-VN')
            print(f"--> [NGHE DUOC]: {text}") # In ra để bạn biết nó nghe thấy gì
            return text.lower()

        except sr.WaitTimeoutError:
            return "" 
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"[LOI TAI] {e}")
            return ""