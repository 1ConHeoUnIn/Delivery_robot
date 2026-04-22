```mermaid
graph TD
    Start([Bắt đầu]) --> Init["Khởi tạo Camera, YOLOv8, MediaPipe, Model LBPH"]
    Init --> ReadFrame[/"Đọc Frame từ Camera"/]
    
    ReadFrame --> CheckPerson{"YOLO nhận diện<br/>được Người?"}
    CheckPerson -- Không --> CmdS1["Lệnh Dừng: S"]
    
    CheckPerson -- Có --> CheckMaster{"Là MASTER?<br/>(Sai số LBPH < 75)"}
    CheckMaster -- Không --> CmdS2["Lệnh Dừng: S<br/>Phát loa: 'Người lạ'"]
    
    CheckMaster -- Có --> CheckHand{"MediaPipe:<br/>Sếp có giơ tay?"}
    CheckHand -- Có --> CmdB["Lệnh Lùi: B"]
    
    CheckHand -- Không --> CheckX{"Lệch trục X > 0.1?<br/>(Cần bẻ lái)"}
    CheckX -- Có --> CmdTurn["Lệnh Rẽ Arc-Turn:<br/>L hoặc R với min_speed"]
    
    CheckX -- Không --> CheckZClose{"Khung hình > brake_ratio?<br/>(Đứng quá gần)"}
    CheckZClose -- Có --> CmdS3["Lệnh Dừng: S<br/>Reset Khâu I = 0"]
    
    CheckZClose -- Không --> CheckZFar{"Khung hình < safe_distance?<br/>(Đứng xa / Bị kẹt gờ)"}
    CheckZFar -- Có --> BoostUp["Nạp ga:<br/>integral_boost += 1.5"]
    CheckZFar -- Không --> BoostDown["Xả ga:<br/>integral_boost -= 3.0"]
    
    BoostUp --> CalcSpeed["Tính toán lực kéo:<br/>base_speed = cruise_speed + integral_boost"]
    BoostDown --> CalcSpeed
    CalcSpeed --> CmdW["Lệnh Tiến:<br/>W + base_speed"]
    
    CmdS1 --> Filter
    CmdS2 --> Filter
    CmdB --> Filter
    CmdTurn --> Filter
    CmdS3 --> Filter
    CmdW --> Filter
    
    Filter{"Bộ lọc Anti-Spam UDP:<br/>Đổi lệnh hướng HOẶC<br/>Chênh lệch tốc độ >= 5?"}
    Filter -- Có --> Send[/"Gửi lệnh UDP<br/>xuống ESP32"/]
    Filter -- Không --> Skip["Bỏ qua, không gửi"]
    
    Send --> ReadFrame
    Skip --> ReadFrame 
    ```