import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='okas')
cur = conn.cursor()
cur.execute("DROP DATABASE IF EXISTS okascloud")
cur.execute("CREATE DATABASE okascloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cur.execute("GRANT ALL PRIVILEGES ON okascloud.* TO 'okasdev'@'%'")
cur.execute("FLUSH PRIVILEGES")
conn.commit()
print("Database reset OK")
conn.close()
