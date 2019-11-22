# Session 8 - ACID

Grading: 1pt

## Setup

```
docker run -p 5432:5432 fiitpdt/postgres
```

## Labs

Try benchmarking PostgreSQL write performance with and without synchronous_commit option set.
The metric that you should measure is inserts per seconds - i.e., how many inserts can the database process in 1 second.

I implemented my own python script with simple benchmark for one second:
```python
import psycopg2
import time
import random

con = psycopg2.connect(database="oz", user="postgres", password="", host="127.0.0.1", port="5432")
cur = con.cursor()

a = time.time()
counter = 0
while time.time() - a < 1:
    doc_id = random.randint(1,10001)
    t = time.perf_counter()
    cur.execute(f"insert into documents(name, type, created_at, department, contracted_amount) values ('Generated doc {doc_id}', 'MyType', now(), 'Department #{doc_id}', {doc_id})")
    con.commit()
    counter += 1 
    elapsed = time.perf_counter() - t
    print(f'Time {elapsed:0.4}')


print(f"Insterted {counter} in one sec")
con.close()
```

Results:
```
Insterted 248 in one sec
```

**Stop the docker container and run it again, but with different options.**

```sh
docker run -p 5432:5432 fiitpdt/postgres postgres -c 'synchronous_commit=off'
```

> The above command will run the docker container, but it will explicitely launch  `postgres` command, and pass it a configuration option via the `-c` parameter, which will disable synchronous commit.

Run the benchmark again. How many inserts per second can it handle now?

Here is the raw output of my script:
```
Insterted 290 in one sec
```

### Summary
The difference between synchronous_commit `on` and `off` is about 42 inserts i think that difference is caused mainly by short execution time