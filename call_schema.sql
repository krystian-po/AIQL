DROP TABLE IF EXISTS calls;

CREATE TABLE calls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME,
    duration_minutes FLOAT,
    origin_country VARCHAR(50),
    destination_country VARCHAR(50),
    call_type ENUM('incoming', 'outgoing')
);