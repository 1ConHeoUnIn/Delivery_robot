#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "Motor_control.h" 

// --- CẤU HÌNH WIFI ---
const char* ssid = "H";
const char* password = "........";

// --- CẤU HÌNH UDP ---
WiFiUDP udp;
unsigned int localPort = 4210;
char packetBuffer[255];

// --- KHỞI TẠO ĐỐI TƯỢNG ROBOT ---
motor_driver robot; 

// --- CẤU HÌNH TỐC ĐỘ ---
const int SPEED_NORMAL = 85; 
const int SPEED_TURN   = 65; 

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
    
    // In ra Serial để mài dễ giám sát
    Serial.print("Lenh nhan duoc: "); 
    Serial.println(message); 

    // --- LOGIC MỚI: BÓC TÁCH CHỮ VÀ SỐ ---
    if (message.length() > 0) {
      char cmdType = message.charAt(0); // Lấy đúng chữ cái đầu tiên (S, W, B, L, R)
      
      // Mặc định tốc độ (nếu Python không gửi số kèm theo, ví dụ lệnh "W" hay "B")
      int currentSpeed = SPEED_NORMAL; 
      
      // Nếu chuỗi dài hơn 1 ký tự (VD: "L150"), thì cắt lấy phần số phía sau
      if (message.length() > 1) {
        currentSpeed = message.substring(1).toInt();
      } else if (cmdType == 'L' || cmdType == 'R') {
        // Nếu lỡ Python chỉ gửi "L" trần trụi, thì xài tốc độ quay mặc định của mài
        currentSpeed = SPEED_TURN;
      }

      // --- XỬ LÝ LỆNH VÀ TRUYỀN TỐC ĐỘ VÀO MOTOR ---
      if (cmdType == 'S') {
        robot.stop();
      } 
      else if (cmdType == 'L') {
        robot.turn_left(currentSpeed); // Quay trái với tốc độ AI tính toán
      } 
      else if (cmdType == 'R') {
        robot.turn_right(currentSpeed); // Quay phải với tốc độ AI tính toán
      }
      else if (cmdType == 'W') { 
        robot.move_forward(currentSpeed);
      }
      else if (cmdType == 'B') {
        robot.move_backward(currentSpeed);
      }
    }
  }
}