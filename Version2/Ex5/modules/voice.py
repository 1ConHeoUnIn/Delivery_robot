import pyttsx3
import threading

class AndroidVoice:
    def __init__(self):
        # Khởi tạo engine giọng nói
        self.engine = pyttsx3.init()
        
        # Cấu hình giọng nói
        voices = self.engine.getProperty('voices')
        self.voice_id = None
        
        # Cố gắng tìm giọng tiếng Việt (nếu máy có cài)
        for voice in voices:
            if "Vietnam" in voice.name or "An" in voice.name:
                self.voice_id = voice.id
                break
        
        # Cấu hình tốc độ và âm lượng
        if self.voice_id:
            self.engine.setProperty('voice', self.voice_id)
        
        self.engine.setProperty('rate', 150)   # Tốc độ nói
        self.engine.setProperty('volume', 1.0) # Âm lượng to nhất

    def say(self, text):
        """Hàm này tạo luồng riêng để nói, tránh làm đơ Camera"""
        threading.Thread(target=self._speak_thread, args=(text,)).start()

    def _speak_thread(self, text):
        try:
            # Tạo engine cục bộ cho mỗi luồng để tránh xung đột luồng
            engine = pyttsx3.init()
            if self.voice_id:
                engine.setProperty('voice', self.voice_id)
            engine.setProperty('rate', 150)
            
            print(f"[LOA] Dang noi: {text}")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[LOI GIONG NOI] {e}")