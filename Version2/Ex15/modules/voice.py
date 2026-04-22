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
        
        # --- FIX: THÊM Ổ KHÓA CHỐNG SPAM MẠNG ---
        self.is_downloading = False 

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
        """Kiểm tra xem loa có đang bận nói HOẶC mạng đang bận tải không"""
        if not self.has_audio: return False
        try:
            # Sửa: Trả về True nếu ĐANG TẢI hoặc ĐANG PHÁT TIẾNG
            return self.is_downloading or pygame.mixer.music.get_busy()
        except:
            return False

    def say(self, text):
        if not self.has_audio: return
        
        # Nếu đang bận thì dội ngược lệnh ngay, không cho đẻ luồng mới
        if self.is_busy():
            return
            
        # SẬP Ổ KHÓA LẠI NGAY LẬP TỨC
        self.is_downloading = True 
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
                # Đợi nói xong mới thoát vòng lặp
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"[LOI LOA] {e}")
            
        finally:
            # TẢI VÀ NÓI XONG THÌ MỞ KHÓA CHO LẦN SAU
            self.is_downloading = False