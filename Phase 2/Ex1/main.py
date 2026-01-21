from modules.communication import RobotWiFi

def main():
    print("--- KHOI DONG HE THONG (MANUAL IP) ---")
    
    # 1. Nhập IP thủ công (Lấy từ Serial Monitor của ESP32)
    # Ví dụ: 192.168.2.13
    robot_ip = input("Nhap IP cua Robot (xem tren Serial Monitor): ").strip()
    
    if not robot_ip:
        print("Loi: Ban chua nhap IP!")
        return

    # 2. Kết nối
    robot = RobotWiFi(ip=robot_ip, port=4210)
    
    print(f"\nDa san sang! Nhap lenh: W, S, L, R, B (Q de thoat)")
    
    while True:
        key = input("Lenh >> ").upper().strip()
        
        if key == "Q":
            break
        elif key in ["W", "S", "L", "R", "B"]:
            robot.send_command(key)
        else:
            print("Lenh khong hop le (Chi nhan W, S, L, R, B)")

    # Dọn dẹp
    robot.close()

if __name__ == "__main__":
    main()