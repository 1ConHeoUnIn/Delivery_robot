#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "Motor_control.h" // Nhúng thư viện điều khiển động cơ của bạn

// --- CẤU HÌNH WIFI ---
const char* ssid = "Huu Ngan 5G";
const char* password = "22222222H";

// --- CẤU HÌNH UDP ---
WiFiUDP udp;
unsigned int localPort = 4210;
char packetBuffer[255];

// --- KHỞI TẠO ĐỐI TƯỢNG ROBOT ---
motor_driver robot; 

// --- CẤU HÌNH TỐC ĐỘ ---
// Lưu ý: Trong Motor_control.cpp bạn cài đặt độ phân giải 9-bit
// Giá trị tốc độ chạy từ 0 đến 511.
const int SPEED_NORMAL = 400; // Tốc độ chạy thẳng
const int SPEED_TURN   = 350; // Tốc độ khi quay

void setup() {
  Serial.begin(115200);

  // 1. Khởi động phần điều khiển động cơ
  robot.begin();
  Serial.println("Khoi dong Motor Driver thanh cong!");

  // 2. Kết nối WiFi
  Serial.print("Dang ket noi WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi da ket noi!");
  Serial.print("IP cua ESP32: ");
  Serial.println(WiFi.localIP()); 

  // 3. Bắt đầu lắng nghe UDP
  udp.begin(localPort);
  Serial.printf("Dang lang nghe UDP tai cong %d\n", localPort);
}

void loop() {
  // Kiểm tra gói tin UDP đến
  int packetSize = udp.parsePacket();
  
  if (packetSize) {
    // Đọc dữ liệu
    int len = udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = 0; // Kết thúc chuỗi
    }
    
    String message = String(packetBuffer);
    
    // Xóa khoảng trắng thừa (nếu có) để so sánh chính xác
    message.trim(); 
    
    Serial.print("Lenh nhan duoc: ");
    Serial.println(message);

    // --- XỬ LÝ LỆNH ---
    
    if (message == "S") {
      robot.stop();
      Serial.println("-> DUNG LAI");
    } 
    else if (message == "L") {
      robot.turn_left(SPEED_TURN);
      Serial.println("-> QUAY TRAI");
    } 
    else if (message == "R") {
      robot.turn_right(SPEED_TURN);
      Serial.println("-> QUAY PHAI");
    }
    // Lệnh từ bàn phím hoặc mở rộng
    else if (message == "W" || message == "ON") { 
      robot.move_forward(SPEED_NORMAL);
      Serial.println("-> DI THANG");
    }
    else if (message == "B") {
      robot.move_backward(SPEED_NORMAL);
      Serial.println("-> DI LUI");
    }
  }
}