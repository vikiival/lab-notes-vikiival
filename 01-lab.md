## Lab 1 - Query plans & indexing

### **1. Setup**

Installing docker with `brew cask install docker`
For running docker I wrote script

```bash
#!/bin/bash

brew services stop postgresql;
docker run -p 5432:5432 fiitpdt/postgres
```

In new terminal run

```
psql -U postgres -h localhost -p 5432 -d oz
```

### **2. Try how indexes make a query faster**

**Write a simple query filtering on a single column (e.g. supplier = '', or department = ''). Measure how long the query takes.**

I used query `explain analyse select * from documents where supplier = '100matolog, s.r.o.';`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 93.641             |
| 2       | 99.509             |
| 3       | 93.501             |
| 4       | 94.340             |
| 5       | 93.780             |
| 6       | 97.609             |
|         |                    |
| Average | 95.3966666667      |

```
                          QUERY PLAN
---------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..17398.30 rows=8 width=304)
   Filter: ((supplier)::text = '100matolog, s.r.o.'::text)
(2 rows)
```

**Add an index for the column and measure how fast is the query now. What plan did the database use before & after index?**

Added index using `create index supplier_index on documents (supplier);`
I used query `explain analyse select * from documents where supplier = '100matolog, s.r.o.';`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 0.064              |
| 2       | 0.052              |
| 3       | 0.064              |
| 4       | 0.065              |
| 5       | 0.079              |
| 6       | 0.070              |
|         |                    |
| Average | 0.06566666667      |

```
                                 QUERY PLAN
-----------------------------------------------------------------------------
 Bitmap Heap Scan on documents  (cost=4.48..35.99 rows=8 width=304)
   Recheck Cond: ((supplier)::text = '100matolog, s.r.o.'::text)
   ->  Bitmap Index Scan on supplier_index  (cost=0.00..4.48 rows=8 width=0)
         Index Cond: ((supplier)::text = '100matolog, s.r.o.'::text)
(4 rows)
```

Hint: To delete index use `drop index supplier_index;`

**Write a simple range query on a single column (e.g., total_amount > 100000 and total_amount <= 999999999). Measure how long the query takes.**

To find interval that can be used I ran
`select min(contracted_amount), max(contracted_amount) from documents;`

result
| min | max |
|--------+------------|
| -32929 | 1300000000 |

so then we called
`explain analyse select * from documents where contracted_amount > 10000 and contracted_amount < 9999999;`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 129.322            |
| 2       | 117.633            |
| 3       | 116.449            |
| 4       | 119.185            |
| 5       | 114.876            |
| 6       | 117.375            |
|         |                    |
| Average | 119.14             |

```
                                                    QUERY PLAN
-------------------------------------------------------------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..18276.36 rows=46442 width=304) (actual time=1.022..127.014 rows=46488 loops=1)
   Filter: ((contracted_amount > 10000::double precision) AND (contracted_amount < 9999999::double precision))
   Rows Removed by Filter: 304736
(4 rows)
```

**Add an index for the column and measure how fast is the query now. What plan did the database use before & after index?**

Added index using `create index contracted_amount_index on documents(contracted_amount);`
I used query
`explain analyse select * from documents where contracted_amount > 10000 and contracted_amount < 9999999;`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 356.761            |
| 2       | 28.873             |
| 3       | 26.449             |
| 4       | 29.383             |
| 5       | 30.304             |
| 6       | 29.799             |
|         |                    |
| Average | 88.3065            |

```
                                                                QUERY PLAN
------------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on documents  (cost=988.26..14692.60 rows=46423 width=304) (actual time=11.500..353.794 rows=46488 loops=1)
   Recheck Cond: ((contracted_amount > 10000::double precision) AND (contracted_amount < 9999999::double precision))
   ->  Bitmap Index Scan on contracted_amount_index  (cost=0.00..976.65 rows=46423 width=0) (actual time=9.630..9.630 rows=46488 loops=1)
         Index Cond: ((contracted_amount > 10000::double precision) AND (contracted_amount < 9999999::double precision))
(5 rows)
```

### **3. Try how indexes slow down writes**

**Drop all indexes on the `documents` table.**

To drop indexes use
`drop index supplier_index;` and `drop index contracted_amount_index;`

**Benchmark how long does it take to insert a batch of N rows into the `documents` table.**

We need to find how long does it take add 1024 record into database
I used query `explain analyse insert into documents (select * from documents limit 1000);`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 5.847              |
| 2       | 3.331              |
| 3       | 4.746              |
| 4       | 3.759              |
| 5       | 6.833              |
| 6       | 7.429              |
|         |                    |
| Average | 5.3241666667       |

```
                                                               QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------------
 Insert on documents  (cost=0.00..57.04 rows=1000 width=304) (actual time=7.565..7.565 rows=0 loops=1)
   ->  Limit  (cost=0.00..47.04 rows=1000 width=304) (actual time=0.033..0.624 rows=1000 loops=1)
         ->  Seq Scan on documents documents_1  (cost=0.00..16520.24 rows=351224 width=304) (actual time=0.032..0.517 rows=1000 loops=1)
(4 rows)
```

**Create index on a single column in the `documents` table. Choose an arbitrary column.**

Added index using `create index supplier_index on documents (supplier);`

**Benchmark how long does it take to insert a batch of N rows now. How much slower is the insert now?**

I used query `explain analyse insert into documents (select * from documents limit 1000);`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 44.938             |
| 2       | 34.285             |
| 3       | 31.270             |
| 4       | 24.278             |
| 5       | 20.968             |
| 6       | 23.483             |
|         |                    |
| Average | 29.870333333333335 |

As we see after adding indexes query is 5 times slower. We assume than adding more than 1000 elements per query would have greater inpact on performance.

**Repeat the benchmark with 2 indices and 3 indices.**

Added index on column `supplier_ico` using `create index supplier_ico_index on documents(supplier_ico);`
I used query `explain analyse insert into documents (select * from documents limit 1000);`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 86.335             |
| 2       | 45.835             |
| 3       | 41.836             |
| 4       | 42.667             |
| 5       | 54.277             |
| 6       | 42.915             |
|         |                    |
| Average | 52.310833333333335 |

I added another index on column `name` using `create index name_index on documents(name);`
I used query `explain analyse insert into documents (select * from documents limit 1000);`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 155.734            |
| 2       | 124.643            |
| 3       | 121.913            |
| 4       | 117.310            |
| 5       | 113.746            |
| 6       | 100.014            |
|         |                    |
| Average | 122.22666666666667 |

After using second index query run about 2 times longer. Using third index query ran about 4 times longer than using only one index.

**Now drop all indices and try if there's a difference in insert performance when you have a single index over low cardinality column vs. high cardinality column.**

> Theory: In the context of databases, cardinality refers to the uniqueness of data values contained in a column. _High cardinality_ means that the column contains a large percentage of totally unique values. _Low cardinality_ means that the column contains a lot of “repeats” in its data range.

To drop all indexes just use
`drop index supplier_index;`
`drop index supplier_ico_index;`
`drop index name_index;`

I used query `explain analyse insert into documents (select * from documents limit 1000);`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 3.242              |
| 2       | 2.412              |
| 3       | 3.178              |
| 4       | 5.796              |
| 5       | 4.769              |
| 6       | 3.193              |
|         |                    |
| Average | 3.765              |

Without indexes insert is about 10 times faster than insert with one index.

Cardinalities
I used two selects
`select count(DISTINCT id), count(DISTINCT name), count(DISTINCT type), count(DISTINCT created_at), count(DISTINCT department), count(DISTINCT customer), count(DISTINCT supplier), count(DISTINCT supplier_ico), count(DISTINCT contracted_amount), count(DISTINCT total_amount), count(DISTINCT published_on), count(DISTINCT effective_from), count(DISTINCT expires_on), count(DISTINCT note), count(DISTINCT pocet_stran), count(DISTINCT source) from documents;`

`select count(id), count(name), count(type), count(created_at), count(department), count(customer), count(supplier), count(supplier_ico), count(contracted_amount), count(total_amount), count(published_on), count(effective_from), count(expires_on), count(note), count(pocet_stran), count(source) from documents;`

> use script for generating such a long query in JS it's like 5 lines of code

|       | id     | name   | type   | created_at | department | customer | supplier | supplier_ico | contracted_amount | total_amount | published_on | effective_from | expires_on | note  | pocet_stran | source |
| ----- | ------ | ------ | ------ | ---------- | ---------- | -------- | -------- | ------------ | ----------------- | ------------ | ------------ | -------------- | ---------- | ----- | ----------- | ------ |
| count | 382224 | 382224 | 382224 | 382224     | 348271     | 382224   | 382224   | 274993       | 364029            | 365667       | 368823       | 376993         | 144326     | 63620 | 382224      | 382224 |
| dist  | 341965 | 129030 | 4      | 341960     | 84         | 39565    | 138789   | 44641        | 51289             | 50731        | 745          | 928            | 3017       | 16949 | 297         | 2      |

So we selected `name` as high cardinality column.
Added index using `create index name on documents(name);`

I used query `explain analyse insert into documents (select * from documents limit 1000);`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 60.334             |
| 2       | 57.007             |
| 3       | 59.853             |
| 4       | 55.001             |
| 5       | 61.682             |
| 6       | 62.487             |
|         |                    |
| Average | 59.394000000000005 |


Then I deleted index using `drop index name_index ;`


As low cardinality column we chose `source`

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 14.249|
| 2       | 13.022|
| 3       | 18.413|
| 4       | 12.178|
| 5       | 15.047|
| 6       | 14.387|
|         |                    |
| Average | 14.549333333333331 |

As we can see from the tables adding index on _low cardinality column_ is faster than _high cardinality column_.

### Summary

In this lab we learned:
- How indexes change the work of database 
- That using index on table speeds up query but slows down insert
