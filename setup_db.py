import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='okas')
cur = conn.cursor()
cur.execute("CREATE DATABASE IF NOT EXISTS okascloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cur.execute("CREATE USER IF NOT EXISTS 'okasdev'@'%' IDENTIFIED BY 'okas'")
cur.execute("GRANT ALL PRIVILEGES ON okascloud.* TO 'okasdev'@'%'")
cur.execute("FLUSH PRIVILEGES")
conn.commit()
print("DB and user created OK")
conn.close()
