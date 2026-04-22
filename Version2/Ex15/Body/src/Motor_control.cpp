//Motor_control.cpp
#include "Motor_control.h"

motor_driver::motor_driver(){}

void motor_driver::begin() {
    // Gán kênh PWM cho từng chân
    ledcSetup(0, 10000, 9); // kênh 0, tần số 10kHz, độ phân giải 9bit
    ledcSetup(1, 10000, 9);
    ledcSetup(2, 10000, 9);
    ledcSetup(3, 10000, 9);
    
    ledcAttachPin(PinManager::in1, 0);
    ledcAttachPin(PinManager::in2, 1);
    ledcAttachPin(PinManager::in3, 2);
    ledcAttachPin(PinManager::in4, 3);
    stop(); 
}

void motor_driver::move_forward(int speed) {
    smooth_transition(speed, 0, speed, 0);
}

void motor_driver::move_backward(int speed) {
    smooth_transition(0, speed, 0, speed);
}

// --- [FIX TỬ HUYỆT CƠ KHÍ LEO GỜ] ---
// Đổi từ Quay Tại Chỗ (Pivot Turn) sang Quay Vòng Cung (Arc Turn)
void motor_driver::turn_left(int speed) {
    // Để rẽ trái: Bánh trái chạy 40%, Bánh phải chạy 100% công suất
    // Giúp 2 bánh CÙNG ĐẨY LÊN TRƯỚC để thoát gờ giảm tốc thay vì lùi lại
    smooth_transition(speed * 0.4, 0, speed, 0);
}

void motor_driver::turn_right(int speed) {
    // Để rẽ phải: Bánh trái chạy 100%, Bánh phải chạy 40% công suất
    smooth_transition(speed, 0, speed * 0.4, 0);
}

void motor_driver::turn_back_left(int speed) {
    smooth_transition(0, speed * 0.4, 0, speed);
}

void motor_driver::turn_back_right(int speed) {
    smooth_transition(0, speed, 0, speed * 0.4);
}

void motor_driver::stop() {
    smooth_transition(0, 0, 0, 0); 
}

// --- HÀM XỬ LÝ TĂNG/GIẢM TỐC MƯỢT MÀ ---
void motor_driver::smooth_transition(int t0, int t1, int t2, int t3) {
    int step = 4;      
    int delay_ms = 2;  
    
    while (cur_pwm[0] != t0 || cur_pwm[1] != t1 || cur_pwm[2] != t2 || cur_pwm[3] != t3) {
        if (cur_pwm[0] < t0) cur_pwm[0] = min(cur_pwm[0] + step, t0);
        else if (cur_pwm[0] > t0) cur_pwm[0] = max(cur_pwm[0] - step, t0);
        
        if (cur_pwm[1] < t1) cur_pwm[1] = min(cur_pwm[1] + step, t1);
        else if (cur_pwm[1] > t1) cur_pwm[1] = max(cur_pwm[1] - step, t1);
        
        if (cur_pwm[2] < t2) cur_pwm[2] = min(cur_pwm[2] + step, t2);
        else if (cur_pwm[2] > t2) cur_pwm[2] = max(cur_pwm[2] - step, t2);
        
        if (cur_pwm[3] < t3) cur_pwm[3] = min(cur_pwm[3] + step, t3);
        else if (cur_pwm[3] > t3) cur_pwm[3] = max(cur_pwm[3] - step, t3);
        
        ledcWrite(0, cur_pwm[0]);
        ledcWrite(1, cur_pwm[1]);
        ledcWrite(2, cur_pwm[2]);
        ledcWrite(3, cur_pwm[3]);
        delay(delay_ms);
    }
}