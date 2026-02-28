// pin_manager.h
#ifndef PIN_MANAGER_H
#define PIN_MANAGER_H
#include <Wire.h>
#include <HardwareSerial.h>

struct PinManager {
    // I2C (Đổi sang 3 và 4 vì chân 0 là nút BOOT trên S3)
    static const int SDA = 3;
    static const int SCL = 4;

    // MOTOR (Gom chung vào 1 hàng dưới của mạch cho dễ cắm dây)
    static const int in1 = 8;  // A+
    static const int in2 = 9;  // A-
    static const int in3 = 10; // B+
    static const int in4 = 11; // B-

    // UART (Chân TX, RX thực tế in trên board Super Mini)
    static const int UART_TX = 43;
    static const int UART_RX = 44;

    static void init_i2c() {
        Wire.begin(SDA, SCL);
    }
};
#endif