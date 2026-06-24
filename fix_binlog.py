import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='okas')
cur = conn.cursor()
cur.execute("SET GLOBAL log_bin_trust_function_creators = 1")
cur.execute("GRANT SUPER ON *.* TO 'okasdev'@'%'")
cur.execute("FLUSH PRIVILEGES")
conn.commit()
print("Done")
conn.close()
