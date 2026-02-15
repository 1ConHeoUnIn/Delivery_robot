// pin_manager.h
#ifndef PIN_MANAGER_H
#define PIN_MANAGER_H
#include<Wire.h>
#include <HardwareSerial.h>

//  Cấu hình chân dùng chung
struct PinManager {
    // I2C 
    static const int SDA = 0;
    static const int SCL = 1;
    //motor
    static const int in1 = 8; //A+
    static const int in2 = 7; //A-

    static const int in3 = 6; // B+
    static const int in4 = 5; // B-
    
    //UART
   static const int UART_TX = 21;
   static const int UART_RX = 20;


    
    static void init_i2c()
    {
        Wire.begin(SDA, SCL);
    }
   
};

#endif
