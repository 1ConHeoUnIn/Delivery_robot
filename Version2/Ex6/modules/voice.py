from gtts import gTTS
import os
import hashlib
import pygame
import threading
import time

class AndroidVoice:
    def __init__(self):
        # Tắt thông báo của pygame
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
        try:
            pygame.mixer.init()
            self.has_audio = True
        except:
            print("[LOA] Loi khoi tao am thanh! Robot se bi cam.")
            self.has_audio = False
        
        # Thư mục Cache
        self.cache_dir = r"D:\Upgrade project\Version2\Memory\voice_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        print("[LOA] Khoi dong che do Giong Noi Online (Google TTS)")

    def is_busy(self):
        """Kiểm tra xem loa có đang bận nói không"""
        if not self.has_audio: return False
        try:
            return pygame.mixer.music.get_busy()
        except:
            return False

    def say(self, text):
        """Chỉ nói nếu loa đang rảnh"""
        if not self.has_audio: return

        # [QUAN TRỌNG] Nếu đang bận nói câu trước -> Bỏ qua câu mới luôn
        if self.is_busy():
            return 

        threading.Thread(target=self._speak_thread, args=(text,)).start()

    def _speak_thread(self, text):
        try:
            filename_hash = hashlib.md5(text.encode()).hexdigest()
            file_path = os.path.join(self.cache_dir, f"{filename_hash}.mp3")

            # Tải nếu chưa có
            if not os.path.exists(file_path):
                print(f"[GOOGLE TTS] Tai: '{text}'...")
                tts = gTTS(text=text, lang='vi', slow=False)
                tts.save(file_path)
            
            # Phát âm thanh
            if self.has_audio:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                # Đợi nói xong mới giải phóng thread
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

        except Exception as e:
            print(f"[LOI LOA] {e}")