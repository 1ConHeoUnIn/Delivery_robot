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
        # ... (đoạn trên giữ nguyên)
    
        cv2.imshow("ROBOT AI VISION", frame)
        
        # [SỬA] Tăng thời gian chờ từ 1 lên 10ms để dễ bắt phím hơn
        key = cv2.waitKey(10) & 0xFF
        
        # --- PHÍM TẮT ĐIỀU KHIỂN ---
        if key == ord('q'): # Thoát
            print("Da nhan Q -> Thoat")
            break
        
        elif key == ord('n'): # NEW USER
            print("\n[DA NHAN LENH N] -> DANG CHUAN BI HOC...")
            robot.send_command("S") # Dừng xe
            
            # Quan trọng: Đóng cửa sổ camera tạm thời để bạn tập trung vào Terminal
            cv2.destroyAllWindows()
            
            try:
                # Bây giờ mới chuyển qua cửa sổ đen để nhập số
                new_id_input = input(">> HAY NHAP ID MOI (So nguyen): ")
                new_id = int(new_id_input)
                engine.start_learning(new_id)
            except ValueError:
                print("Loi: Ban phai nhap so nguyen (Vi du: 2, 3)!")


    # --- ĐOẠN CODE DỌN DẸP MỚI (FIX LỖI ĐƠ) ---
    print("Dang tat he thong...")
    
    # 1. Dừng robot trước
    robot.close()
    
    # 2. Tắt Camera và AI
    engine.stop()
    
    # 3. QUAN TRỌNG: Ngủ 1 giây để Camera kịp nhả tài nguyên
    time.sleep(1.0) 
    
    # 4. Giờ mới được tắt cửa sổ
    cv2.destroyAllWindows()
    
    # 5. Mẹo nhỏ: Gọi waitKey thêm vài lần để xả hết bộ nhớ đệm đồ họa
    for i in range(5):
        cv2.waitKey(1)
        
    print("Da tat hoan toan.")

if __name__ == "__main__":
    main()        
