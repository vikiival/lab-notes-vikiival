import psycopg2
import time
import random

con = psycopg2.connect(database="oz", user="postgres", password="", host="127.0.0.1", port="5432")
cur = con.cursor()

a = time.time()
counter = 0
while time.time() - a < 1:
    doc_id = random.randint(10001,100001)
    t = time.perf_counter()
    cur.execute(f"insert into documents(name, type, created_at, department, contracted_amount) values ('Generated doc {doc_id}', 'MyType', now(), 'Department #{doc_id}', {doc_id})")
    con.commit()
    counter += 1 
    elapsed = time.perf_counter() - t
    print(f'Time {elapsed:0.4}')


print(f"Insterted {counter} in one sec")
con.close()