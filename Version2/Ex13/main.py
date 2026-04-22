import cv2
import time
from modules.communication import RobotWiFi
from modules.face_engine import FaceEngine

# --- CẤU HÌNH ---
# 1. Camera IP (Sửa lại theo điện thoại của bạn)
VIDEO_URL = "http://192.168.137.23:8080/video"
#VIDEO_URL = 0  #<-- Thay bằng số 0

def main():
    print("--- KHOI DONG HE THONG AI ROBOT  ---")

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
            
        # 3. Hiển thị những gì Robot thấy
        cv2.imshow("ROBOT AI VISION", frame)

        # Tăng thời gian chờ từ 1 lên 10ms để dễ bắt phím hơn
        key = cv2.waitKey(10) & 0xFF

        # --- PHÍM TẮT ĐIỀU KHIỂN ---
        if key == ord('q'): # Thoát
            print("Da nhan Q -> Thoat")
            break
            
        # --- TỔ HỢP PHÍM CALIB LIVE ---
        elif key == ord('u'): # Tăng tốc độ mớm ban đầu
            engine.min_speed = min(150, engine.min_speed + 5)
        elif key == ord('j'): # Giảm tốc độ mớm ban đầu
            engine.min_speed = max(20, engine.min_speed - 5)
        elif key == ord('i'): # Tăng tỉ lệ phanh (Lại gần hơn mới phanh)
            engine.brake_ratio = min(0.9, engine.brake_ratio + 0.05)
        elif key == ord('k'): # Giảm tỉ lệ phanh (Đứng xa đã phanh rồi)
            engine.brake_ratio = max(0.3, engine.brake_ratio - 0.05)

        elif key == ord('n'): # NEW USER
            print("\n[DA NHAN LENH N] -> DANG CHUAN BI HOC...")
            robot.send_command("S") # Dừng xe
            cv2.destroyAllWindows()
            try:
                new_id_input = input(">> HAY NHAP ID MOI (So nguyen): ")
                new_id = int(new_id_input)
                engine.start_learning(new_id)
            except ValueError:
                print("Loi: Ban phai nhap so nguyen (Vi du: 2, 3)!")

    # --- ĐOẠN CODE DỌN DẸP ---
    print("Dang tat he thong...")
    robot.close()
    engine.stop()
    time.sleep(1.0)
    cv2.destroyAllWindows()
    for i in range(5):
        cv2.waitKey(1)
    print("Da tat hoan toan.")

if __name__ == "__main__":
    main()