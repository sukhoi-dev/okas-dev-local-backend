import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='okas')
cur = conn.cursor()
cur.execute("DROP DATABASE IF EXISTS okas_signature")
cur.execute("CREATE DATABASE okas_signature CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cur.execute("FLUSH PRIVILEGES")
conn.commit()
print("Database reset OK")
conn.close()
