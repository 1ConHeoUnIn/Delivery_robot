#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "Motor_control.h" 

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
const int SPEED_NORMAL = 400; 
const int SPEED_TURN   = 350; 

void setup() {
  Serial.begin(115200);
  
  // [FIX] Bắt mạch S3 Super Mini đợi 3 giây để Laptop kịp nhận cổng USB COM
  delay(3000); 

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
  Serial.println(WiFi.localIP());  // <--- LẤY IP MỚI NÀY ĐIỀN VÀO PYTHON NHA MÀI

  // 3. Bắt đầu lắng nghe UDP
  udp.begin(localPort);
  Serial.printf("Dang lang nghe UDP tai cong %d\n", localPort);
}

void loop() {
  // Kiểm tra gói tin UDP đến
  int packetSize = udp.parsePacket();
  
  if (packetSize) {
    int len = udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0; // Kết thúc chuỗi
    
    String message = String(packetBuffer);
    message.trim(); 
    
    // [ĐÃ MỞ KHÓA MÕM] - Để mài nhìn thấy nó nhận lệnh gì trên màn hình
    Serial.print("Lenh: "); 
    Serial.println(message); 

    // --- XỬ LÝ LỆNH ---
    if (message == "S") {
      robot.stop();
    } 
    else if (message == "L") {
      robot.turn_left(SPEED_TURN);
    } 
    else if (message == "R") {
      robot.turn_right(SPEED_TURN);
    }
    else if (message == "W" || message == "ON") { 
      robot.move_forward(SPEED_NORMAL);
    }
    else if (message == "B") {
      robot.move_backward(SPEED_NORMAL);
    }
  }
}