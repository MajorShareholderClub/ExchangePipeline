CREATE USER 'root'@'host.docker.internal' IDENTIFIED BY '123456789';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'host.docker.internal';
FLUSH PRIVILEGES;


ALTER USER 'root' IDENTIFIED WITH 'caching_sha2_password' BY '123456789';
FLUSH PRIVILEGES;
SELECT 'User Authentication Plugin Modified Successfully' AS message;