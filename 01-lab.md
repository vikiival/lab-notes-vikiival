# Lab 1 - Query plans & indexing

**Grading**: 1pt

## Goals

- Install docker and run the provided container. Configure an SQL client of your choice and connect to the database.
- Try indexes and see for yourself how they can make a query faster
- Measure how much indexes slow down writes

## Tasks

### Try how indexes make a query faster

Hints:

- Many clients report query duration. Alterntively, use `explain analyze select ...` to get a measurement.
- Don't trust a single measurement. Repeat measurements N times, remove outliers and use average/median.

#### 1. Write a simple query filtering on a single column (e.g. `supplier = ''`, or `department = ''`). Measure how long the query takes.

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

#### 2. Add an index for the column and measure how fast is the query now. What plan did the database use before & after index?

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

#### 3. Write a simple range query on a single column (e.g., `total_amount > 100000 and total_amount <= 999999999`). Measure how long the query takes.

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 81.014             |
| 2       | 84.088             |
| 3       | 82.166             |
| 4       | 82.976             |
| 5       | 79.467             |
| 6       | 80.963             |
|         |                    |
| Average | 81.779             |

#### 4. Add an index for the column and measure how fast is the query now. What plan did the database use before & after index?

|         | Total runtime (ms) |
| ------- | ------------------ |
| 1       | 81.014             |
| 2       | 84.088             |
| 3       | 82.166             |
| 4       | 82.976             |
| 5       | 79.467             |
| 6       | 80.963             |
|         |                    |
| Average | 81.779             |

#### Summary



### Try how indexes slow down writes

Hints:

- Based on your machine and the data you are inserting, you may need to tune the N (number of rows in batch) to get meaningful sensitivity.
- You can use the `insert into documents() (select from documents limit N)` pattern to quickly insert a batch of rows.
- Many clients report query duration. Alterntively, use `explain analyze insert into ...` to get a measurement.
- Don't trust a single measurement. Repeat measurements N times, remove outliers and use average/median.

* Drop all indexes on the `documents` table
* Benchmark how long does it take to insert a batch of N rows into the `documents` table.
* Create index on a single column in the `documents` table. Choose an arbitrary column.
* Benchmark how long does it take to insert a batch of N rows now. How much slower is the insert now?
* Repeat the benchmark with 2 indices and 3 indices.
* Now drop all indices and try if there's a difference in insert performance when you have a single index over low cardinality column vs. high cardinality column.
