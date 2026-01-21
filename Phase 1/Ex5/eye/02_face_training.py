import cv2
import numpy as np
from PIL import Image # Thư viện xử lý ảnh
import os

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Đường dẫn tới nơi chứa ảnh vừa chụp
path = r"D:\Upgrade project\Memory\dataset"
# Đường dẫn để lưu "bộ não" sau khi học xong
trainer_path = r"D:\Upgrade project\Memory\trainer"

# Kiểm tra thư viện nhận diện khuôn mặt
# Nếu lỗi ở dòng dưới, hãy chạy: pip install opencv-contrib-python
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Hàm lấy dữ liệu ảnh và nhãn (ID)
def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]     
    faceSamples = []
    ids = []

    print(f"[THONG BAO] Dang quet {len(imagePaths)} tam anh trong dataset...")

    for imagePath in imagePaths:
        # Bỏ qua nếu không phải file ảnh (ví dụ file hệ thống)
        if not imagePath.endswith("jpg"):
            continue

        # Đọc ảnh và chuyển sang ảnh xám
        PIL_img = Image.open(imagePath).convert('L') 
        img_numpy = np.array(PIL_img, 'uint8')

        # Lấy ID từ tên file (User.1.20.jpg -> ID là 1)
        # Tách chuỗi theo dấu chấm "."
        try:
            id = int(os.path.split(imagePath)[-1].split(".")[1])
        except Exception as e:
            print(f"Bỏ qua file lỗi: {imagePath}")
            continue

        faces = detector.detectMultiScale(img_numpy)

        for (x, y, w, h) in faces:
            faceSamples.append(img_numpy[y:y+h, x:x+w])
            ids.append(id)

    return faceSamples, ids

print("\n[BAT DAU] Dang day Robot hoc mat cua ban (Training)...")
print("Vui long doi trong giay lat...")

faces, ids = getImagesAndLabels(path)

# Bắt đầu training
recognizer.train(faces, np.array(ids))

# Lưu kết quả vào file trainer.yml
if not os.path.exists(trainer_path):
    os.makedirs(trainer_path)

save_file = os.path.join(trainer_path, "trainer.yml")
recognizer.write(save_file) 

print(f"\n[THANH CONG] Da hoc xong {len(np.unique(ids))} khuon mat.")
print(f"[KET QUA] File tri tue da duoc luu tai: {save_file}")
print("Ban da san sang cho buoc tiep theo: NHAN DIEN!")