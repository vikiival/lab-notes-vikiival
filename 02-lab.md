# Lab 2 - Multicolumn Indices, Joins & Aggregations

Grading: 2pt

## Setup

Use `fiitpdt/postgres` container for this lab. Instructions are included in the Lab #1.

If you want to try the queries from the lecure (optional), you will need another container.

```
docker run -p 5432:5432 fiitpdt/postgres-shakespeare
```

The database with example data is called `shakespeare`, username is `postgres`, password is blank (there is no password). To connect via `psql`, use:

```
psql -U postgres -h localhost -p 5432 -d shakespeare
```

## 1. See how `like` with a leading pattern is slow
Used query `explain analyse select * from documents where  supplier_ico = '36565733';`

```
                                                 QUERY PLAN
------------------------------------------------------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..17398.30 rows=15 width=302) (actual time=0.066..103.321 rows=2 loops=1)
   Filter: ((supplier_ico)::text = '36565733'::text)
   Rows Removed by Filter: 351222
 Total runtime: 103.399 ms
(4 rows)
```

I used query `explain analyse select * from documents where  supplier_ico like '%5733'`

```
                                                 QUERY PLAN
------------------------------------------------------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..17398.30 rows=15 width=302) (actual time=0.064..109.307 rows=5 loops=1)
   Filter: ((supplier_ico)::text ~~ '%5733'::text)
   Rows Removed by Filter: 351219
 Total runtime: 109.436 ms
(4 rows)
```

Then we add index on `supplier_ico` using `create index on documents(supplier_ico text_pattern_ops);`
Now we re-run the queries

`explain analyse select * from documents where  supplier_ico = '36565733';`
```
                                                             QUERY PLAN
------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on documents  (cost=4.54..63.20 rows=15 width=302) (actual time=0.105..0.143 rows=2 loops=1)
   Recheck Cond: ((supplier_ico)::text = '36565733'::text)
   ->  Bitmap Index Scan on documents_supplier_ico_idx  (cost=0.00..4.54 rows=15 width=0) (actual time=0.056..0.056 rows=2 loops=1)
         Index Cond: ((supplier_ico)::text = '36565733'::text)
 Total runtime: 0.254 ms
(5 rows)
```

`explain analyse select * from documents where  supplier_ico like '%5733';`

```
                                                 QUERY PLAN
------------------------------------------------------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..17398.30 rows=15 width=302) (actual time=0.023..106.441 rows=5 loops=1)
   Filter: ((supplier_ico)::text ~~ '%5733'::text)
   Rows Removed by Filter: 351219
 Total runtime: 106.574 ms
(4 rows)
```

As we can see adding index to column along with like syntax has no effect on query. Database had to use Sequence Scan to find suffix 5733 for supplier_ico column. If we would use prefix instead of suffix it would use index scan.

## 2. Try `like` with a trailing pattern

I used `explain analyze select * from documents where supplier_ico like '57%';`

```
                                                              QUERY PLAN
--------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on documents  (cost=6.51..758.77 rows=15 width=302) (actual time=0.117..1.742 rows=40 loops=1)
   Filter: ((supplier_ico)::text ~~ '57%'::text)
   ->  Bitmap Index Scan on documents_supplier_ico_idx  (cost=0.00..6.50 rows=208 width=0) (actual time=0.064..0.064 rows=40 loops=1)
         Index Cond: (((supplier_ico)::text ~>=~ '57'::text) AND ((supplier_ico)::text ~<~ '58'::text))
 Total runtime: 2.443 ms
(5 rows)
```

Then I dropped index with `drop index documents_supplier_ico_idx;`
Same query without index

```
                                                 QUERY PLAN
------------------------------------------------------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..17398.30 rows=15 width=302) (actual time=0.289..97.739 rows=40 loops=1)
   Filter: ((supplier_ico)::text ~~ '57%'::text)
   Rows Removed by Filter: 351184
 Total runtime: 98.238 ms
(4 rows)
```

> Have a look at the query plan and notice the *Index Cond* part. How can you interpret this condition? Try giving different inputs and observe how the like query gets rewritten to a range query. You can run `explain` even with nonsensical inputs, e.g. `supplier_ico like 'Ahoj%'` and you will still see how the planner rewrites the like condition.

Index condition says that it will first look for the data we passed as parameter (e.g. first two char must be >= 57 and < 58) then it will use wildcard. It works the same with `Ahoj` word where data needs to be greater or equal than `Ahoj` and less than `Ahok`.

## 3. Make the suffix search fast

> For a functional index, an index is defined on the result of a function applied to one or more columns of a single table. Functional indexes can be used to obtain fast access to data based on the result of function calls.

For creatng functional index I used `create index on documents(reverse(supplier_ico) text_pattern_ops);`
Now we test query `explain analyze select * from documents where reverse(supplier_ico) like reverse('%5773')`

```
                                                          QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on documents  (cost=42.43..4893.82 rows=1756 width=302) (actual time=0.095..0.544 rows=17 loops=1)
   Filter: (reverse((supplier_ico)::text) ~~ '3775%'::text)
   ->  Bitmap Index Scan on documents_reverse_idx  (cost=0.00..41.99 rows=1756 width=0) (actual time=0.052..0.052 rows=17 loops=1)
         Index Cond: ((reverse((supplier_ico)::text) ~>=~ '3775'::text) AND (reverse((supplier_ico)::text) ~<~ '3776'::text))
 Total runtime: 0.752 ms
(5 rows)
```

> There is a trick that you can use to make the original suffix query fast. If you reverse both the supplier_ico and the input, you can transform the slow suffix search into fast prefix search.



## 4. Optional: Learn more about indexing `like '%x%'` queries

If you want to understand how to properly index `LIKE '%x%'` expressions (and the trade-offs), read

- http://www.depesz.com/2011/02/19/waiting-for-9-1-faster-likeilike/
- http://www.postgresql.org/docs/9.4/static/pgtrgm.html

## 5. Understand covering index

I user query `explain analyze select customer from documents where department = 'Rozhlas a televizia Slovenska';`

``` 
                                                  QUERY PLAN
-------------------------------------------------------------------------------------------------------------------
 Seq Scan on documents  (cost=0.00..17398.30 rows=16074 width=41) (actual time=21.618..273.684 rows=16917 loops=1)
   Filter: ((department)::text = 'Rozhlas a televizia Slovenska'::text)
   Rows Removed by Filter: 334307
 Total runtime: 434.706 ms
(4 rows)
Try building an index on the condition that you need (i.e., index on `deparment` column). Measure how fast is the query without and with this index.
```

then I created signle index for department `create index department_index on documents(department);` and rerun the query 

```
                                                            QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on documents  (cost=613.00..14506.38 rows=16074 width=41) (actual time=4.028..224.485 rows=16917 loops=1)
   Recheck Cond: ((department)::text = 'Rozhlas a televizia Slovenska'::text)
   ->  Bitmap Index Scan on department_index  (cost=0.00..608.98 rows=16074 width=0) (actual time=3.442..3.442 rows=16917 loops=1)
         Index Cond: ((department)::text = 'Rozhlas a televizia Slovenska'::text)
 Total runtime: 391.397 ms
(5 rows)

```

then I created covering and partial index `create index on documents(department, customer) where department  = 'Rozhlas a televizia Slovenska';

then `set enable_bitmapscan=off;` and `set enable_seqscan=off;`


```
                                                                           QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
 Index Only Scan using documents_department_customer_idx on documents  (cost=0.41..40746.38 rows=16074 width=41) (actual time=0.136..190.534 rows=16917 loops=1)
   Index Cond: (department = 'Rozhlas a televizia Slovenska'::text)
   Heap Fetches: 16917
 Total runtime: 355.847 ms
(4 rows)

```

## Summary

In this lab we learned:
- How we should use `like` in queries
- That using functional indexes can be quite usefull.


