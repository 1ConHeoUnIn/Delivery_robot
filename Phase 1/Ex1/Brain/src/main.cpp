#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// --- THAY ĐỔI THÔNG TIN WIFI CỦA BẠN Ở ĐÂY ---
const char* ssid = "Huu Ngan 5G";
const char* password = "22222222H";

WiFiUDP udp;
unsigned int localPort = 4210;      // Cổng giao tiếp (phải trùng với Python)
char packetBuffer[255];             // Bộ đệm để chứa dữ liệu nhận được

#define LED_PIN 8 // Đèn LED tích hợp trên ESP32 (thường là GPIO 2)

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  // Kết nối WiFi
  Serial.print("Dang ket noi WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi da ket noi!");
  Serial.print("IP cua ESP32 la: ");
  Serial.println(WiFi.localIP()); // <--- QUAN TRỌNG: GHI LẠI SỐ IP NÀY

  // Bắt đầu lắng nghe UDP
  udp.begin(localPort);
  Serial.printf("Dang lang nghe UDP tai cong %d\n", localPort);
}

void loop() {
  // Kiểm tra xem có gói tin nào gửi đến không
  int packetSize = udp.parsePacket();
  
  if (packetSize) {
    // Đọc dữ liệu
    int len = udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = 0; // Kết thúc chuỗi ký tự
    }
    
    String message = String(packetBuffer);
    Serial.print("Nhan duoc lenh: ");
    Serial.println(message);

    // Xử lý lệnh đơn giản để test
    if (message == "ON") {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("-> Da BAT den LED");
    } else if (message == "OFF") {
      digitalWrite(LED_PIN, LOW);
      Serial.println("-> Da TAT den LED");
    }
  }
}