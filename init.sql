CREATE TABLE IF NOT EXISTS tickets 
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    full_name VARCHAR(255),   
    facility VARCHAR(255),     
    phone VARCHAR(50),         
    email VARCHAR(255),        
    device_numbers TEXT,       
    device_type VARCHAR(255),  
    emotional_tone VARCHAR(50),
    issue_summary TEXT         
;

-- Добавим тестовую запись
INSERT INTO tickets (full_name, facility, phone, email, device_numbers, device_type, emotional_tone, issue_summary) 
VALUES ('Иванов И.И.', 'Завод №1', '+79991234567', 'ivanov@test.ru', '12345, 67890', 'Газоанализатор X', 'Негатив', 'Прибор не включается после калибровки');