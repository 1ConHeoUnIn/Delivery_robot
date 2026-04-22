import cv2
import time
from modules.communication import RobotWiFi
from modules.face_engine import FaceEngine

# --- CẤU HÌNH ---
VIDEO_URL = "http://192.168.137.209:8080/video"

def main():
    print("--- KHOI DONG HE THONG AI ROBOT  ---")
    
    robot_ip = input("1. Nhap IP Robot (tren Serial Monitor): ").strip()
    if not robot_ip: return
    robot = RobotWiFi(ip=robot_ip, port=4210)
    
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
        frame, command = engine.process_frame()
        if frame is None:
            print("Mat tin hieu Camera!")
            break

        # BỘ LỌC CHỐNG SPAM UDP
        send_it = False
        if command != last_command:
            cmd_type = command[0] if len(command) > 0 else "S"
            last_type = last_command[0] if len(last_command) > 0 else "S"
            
            if cmd_type != last_type:
                send_it = True 
            else:
                try:
                    curr_speed = int(command[1:]) if len(command) > 1 else 0
                    last_speed = int(last_command[1:]) if len(last_command) > 1 else 0
                    if abs(curr_speed - last_speed) >= 5:
                        send_it = True
                except:
                    send_it = True 

        if send_it:
            robot.send_command(command)
            last_command = command

        cv2.imshow("ROBOT AI VISION", frame)
        
        # --- [FIX LAG] TRẢ VỀ 1MS ĐỂ GIẢI PHÓNG LUỒNG VIDEO ---
        key = cv2.waitKey(1) & 0xFF
        
        # --- PHÍM TẮT ĐIỀU KHIỂN ---
        if key == ord('q'): 
            print("Da nhan Q -> Thoat")
            break
            
        elif key == ord('u'): # Tăng tốc độ mớm rẽ ban đầu
            engine.min_speed = min(150, engine.min_speed + 5)
        elif key == ord('j'): # Giảm tốc độ mớm rẽ ban đầu
            engine.min_speed = max(20, engine.min_speed - 5)
            
        elif key == ord('i'): # Tăng tỉ lệ phanh
            engine.brake_ratio = min(0.9, engine.brake_ratio + 0.05)
        elif key == ord('k'): # Giảm tỉ lệ phanh
            engine.brake_ratio = max(0.3, engine.brake_ratio - 0.05)
            
        elif key == ord('n'): 
            print("\n[DA NHAN LENH N] -> DANG CHUAN BI HOC...")
            robot.send_command("S") 
            cv2.destroyAllWindows()
            try:
                new_id_input = input(">> HAY NHAP ID MOI (So nguyen): ")
                new_id = int(new_id_input)
                engine.start_learning(new_id)
            except ValueError:
                print("Loi: Ban phai nhap so nguyen (Vi du: 2, 3)!")

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