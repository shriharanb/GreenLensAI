import psycopg2
import os

users = ["postgres", "shri"]
passwords = ["", "postgres", "password", "root", "shri"]
for u in users:
    for p in passwords:
        try:
            conn = psycopg2.connect(
                dbname="greenlensai",
                user=u,
                password=p,
                host="localhost",
                port="5432"
            )
            print(f"✅ Success with user: '{u}' and password: '{p}'")
            conn.close()
            exit(0)
        except Exception as e:
            print(f"❌ Failed with user: '{u}' and password: '{p}': {e}")
exit(1)
