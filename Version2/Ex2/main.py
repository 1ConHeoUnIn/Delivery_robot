import cv2
import time
from modules.communication import RobotWiFi
from modules.face_engine import FaceEngine

# --- CẤU HÌNH ---
# 1. Camera IP (Sửa lại theo điện thoại của bạn)
VIDEO_URL = "http://192.168.2.18:8080/video"

def main():
    print("--- KHOI DONG HE THONG AI ROBOT (PHASE 6) ---")
    
    # BƯỚC 1: KẾT NỐI WIFI (TỦY SỐNG)
    robot_ip = input("1. Nhap IP Robot (tren Serial Monitor): ").strip()
    if not robot_ip: return
    robot = RobotWiFi(ip=robot_ip, port=4210)
    
    # BƯỚC 2: KHOI DONG AI (BỘ NÃO)
    print("2. Dang khoi dong AI (Face Engine)...")
    try:
        engine = FaceEngine(video_source=VIDEO_URL)
    except Exception as e:
        print(f"Loi Camera: {e}")
        return

    print("\n--- HE THONG SAN SANG! ---")
    print("Nhan 'Q' tren man hinh Camera de thoat.")
    
    last_command = "S"

    while True:
        # 1. AI suy nghĩ và ra lệnh
        frame, command = engine.process_frame()
        
        if frame is None:
            print("Mat tin hieu Camera!")
            break

        # 2. Gửi lệnh xuống Robot (Chỉ gửi khi lệnh thay đổi để đỡ spam)
        if command != last_command:
            robot.send_command(command)
            last_command = command
            # print(f"AI Ra lenh: {command}") # Bỏ comment nếu muốn xem log

        # 3. Hiển thị những gì Robot thấy
        cv2.imshow("ROBOT AI VISION", frame)
        
        # Thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Dọn dẹp
    print("Dang tat he thong...")
    robot.close()
    engine.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()