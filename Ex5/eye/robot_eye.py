import cv2

# ======================================================
# QUAN TRỌNG: Thay số IP này bằng số trên điện thoại bạn
# Ví dụ: "http://192.168.1.9:8080/video"
url = "http://192.168.2.18:8080/video" 
# ======================================================

print("Dang ket noi toi Camera...")
cap = cv2.VideoCapture(url)

# Tải bộ não nhận diện khuôn mặt
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

while True:
    ret, frame = cap.read()
    if not ret:
        print("Khong thay hinh anh! Kiem tra lai IP.")
        break

    # Chuyển ảnh sang đen trắng để AI nhìn rõ hơn
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Quét tìm khuôn mặt
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    # Vẽ khung vuông quanh mặt
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, "MASTER", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Hiện lên màn hình
    cv2.imshow('Mat cua Robot', frame)

    # Bấm phím 'q' trên bàn phím để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()