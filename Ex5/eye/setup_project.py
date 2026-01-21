import os

# --- CẤU HÌNH ĐƯỜNG DẪN GỐC (ABSOLUTE PATH) ---
# Dùng r"..." để Python hiểu đây là đường dẫn Windows (không bị lỗi ký tự đặc biệt)
BASE_DIR = r"D:\Upgrade project\Memory"

# Định nghĩa các thư mục con cần thiết
folders = [
    os.path.join(BASE_DIR, "dataset"),  # D:\Upgrade project\Memory\dataset
    os.path.join(BASE_DIR, "trainer"),  # D:\Upgrade project\Memory\trainer
]

print(f"--- ĐANG KIỂM TRA TẠI: {BASE_DIR} ---")

# 1. Kiểm tra xem thư mục gốc của bạn có tồn tại không
if not os.path.exists(BASE_DIR):
    print(f"[CẢNH BÁO] Thư mục gốc '{BASE_DIR}' chưa tồn tại.")
    create_base = input("Bạn có muốn tạo nó không? (y/n): ")
    if create_base.lower() == 'y':
        os.makedirs(BASE_DIR)
        print("[OK] Đã tạo thư mục gốc.")
    else:
        print("Đã hủy. Vui lòng tạo thư mục thủ công trước.")
        exit()

# 2. Tạo các thư mục con (dataset, trainer)
for folder in folders:
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[OK] Đã tạo mới: {folder}")
        else:
            print(f"[INFO] Đã có sẵn: {folder}")
    except OSError as e:
        print(f"[ERROR] Không thể tạo {folder}. Lỗi: {e}")

# 3. Tạo file trainer.yml rỗng (để giữ chỗ)
trainer_file = os.path.join(BASE_DIR, "trainer", "trainer.yml")
if not os.path.exists(trainer_file):
    try:
        with open(trainer_file, 'w') as f:
            pass 
        print(f"[OK] Đã tạo file não bộ: {trainer_file}")
    except Exception as e:
        print(f"[ERROR] Không thể tạo file .yml: {e}")
else:
    print(f"[INFO] File trainer.yml đã tồn tại.")

print("\n---------------------------------------")
print("CẤU TRÚC BỘ NHỚ HOÀN TẤT:")
print(f"📂 {BASE_DIR}")
print(r" ┣ 📂 dataset (Nơi chứa ảnh khuôn mặt)")
print(r" ┗ 📂 trainer (Nơi chứa file trainer.yml)")