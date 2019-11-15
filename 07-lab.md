# Session 6 - Fulltext

Grading: 2pt

## Setup

```
docker run -p 5432:5432 fiitpdt/postgres-fulltext
psql -U postgres -h localhost -p 5432 -d oz
```

## Labs

#### 1. Implement fulltext search in contracts. The search should be case insensitive and accents insensitive. It should support searching by 
- contract name
- department
- customer
- supplier
- by supplier ICO
- and by contract code (anywhere inside contract code, such as `OIaMIS`)


Create case insensitive search configuration:
```sh
create extension unaccent;
create text search configuration sk(copy = simple);
alter text search configuration sk alter mapping for
word with unaccent, simple;
```
Add trigram
```sh
create extension pg_trgm;
```

For simplicity we will create a materialized view:
> View is like sub-table, Materialized means that view is also stored
```sql
create materialized view search_request as
(
    select id,
       to_tsvector('sk', name || ' ' || department || ' ' || customer || ' ' || supplier) as vector,
       supplier_ico::text as supplier_ico,
       published_on,
       identifier
    from contracts
);
```

Added Fast inverted indexes for ico, identifier and vector:
```sql
create index index_request_identifier on search_request using gin(identifier gin_trgm_ops);
create index index_request_supplier_ico on search_request using gin(supplier_ico gin_trgm_ops);
create index index_request_vector on search_request using gin(vector);
```

Create select for full text search, note that supplier_ico and identifier needs to be searched separately because of trigram indexes:
```sql
select c.*
from search_request req
join contracts c on c.id = req.id
where vector @@ to_tsquery('sk', 'oracle') or req.identifier like '%Z38%' or req.supplier_ico like '%0721%'
```

for optimalization we add indexes on id:
```sql
create index index_contracts_id on contracts(id);
create index index_request_id on search_request(id);
```



#### 2. Boost newer contracts, so they have a higher chance of being at top positions.

As boosting algorithm we took rank and divided it by days between `now()` and `published_on` divide by 365(normalization)

```sql
select
       c.*,
       ts_rank(vector, to_tsquery('sk', 'oracle')) as rank
from search_request req
join contracts c on c.id = req.id
where vector @@ to_tsquery('sk', 'oracle') or req.identifier like '%Z38%' or req.supplier_ico like '%0721%'
order by ts_rank(vector, to_tsquery('sk', 'oracle')) / (extract(days from (now() - req.published_on)) / 365) desc;
```

#### 3. Try to find some limitations of your solutions - find a few queries (2 cases are enough) that are not showing expected results, or worse, are not showing any results. Think about why it's happening and propose a solution (no need to implement it).

Väčšina limitácií pri tomto fulltextovom vyhľadávaní je kvôli slovenčine. Hlavný problém je skloňovanie. Nasledujúca query nájde nájomné zmluvy, ale zmluvy o nájme už nie. Ak by boli slová v základnom tvare, tak výsledkov bolo oveľa viac.
The biggest limitation in our solution is Slovak Language. We targeted word flexing as the main problem.
As an example we can use words `kúpna zmluva` which has same meaning as `zmluva & kúpe`. If we were able to stem the words we would find more results.

```sql
select c.*
from search_request req
join contracts c on c.id = req.id
where vector @@ to_tsquery('sk', 'zmluva & kúpe')
```

Also there is problem with correctly quering identifier for example if we knew that identifier has something with `134` in year `2011` the correct query that needs to be used is `134/2011`. Maybe users would like to also search for `134 2011` which does not work.

```sql
select c.name, c.department, c.supplier, c.identifier
from search_request req
join contracts c on c.id = req.id
where req.identifier like '%134/2011%'
```



Hints:

> The data is in slovak, so you will need to use an appropriate dictionary. Type \dF inside `psql` to see available configurations for your installation. There's no support for slovak language, don't worry about it, just create an unaccenting configuration based on the `simple` configuration.
   ```
    oz=# \dF
                  List of text search configurations
      Schema   |    Name    |              Description
    ------------+------------+---------------------------------------
    pg_catalog | danish     | configuration for danish language
    pg_catalog | dutch      | configuration for dutch language
    pg_catalog | english    | configuration for english language
    pg_catalog | finnish    | configuration for finnish language
    pg_catalog | french     | configuration for french language
    pg_catalog | german     | configuration for german language
    pg_catalog | hungarian  | configuration for hungarian language
    pg_catalog | italian    | configuration for italian language
    pg_catalog | norwegian  | configuration for norwegian language
    pg_catalog | portuguese | configuration for portuguese language
    pg_catalog | romanian   | configuration for romanian language
    pg_catalog | russian    | configuration for russian language
    pg_catalog | simple     | simple configuration
    pg_catalog | spanish    | configuration for spanish language
    pg_catalog | swedish    | configuration for swedish language
    pg_catalog | turkish    | configuration for turkish language
   ```
> To implement boosting, you must combine (e.g. multiply) the fulltext score with a boosting value. Since you want to boost by "freshness", compute a difference of current date and the `published_on` date. The result will be an `interval` datatype, which you want to convert to number of days, e.g. `extract(days from (now() - published_on))`. You will need to apply some smoothing functions or other rescaling to the number of days to dampen its impact and retain the value of fulltext score.

> Searching by ICO will require a different kind of processing. You query will need to have (at least) 2 parts - one handling the fulltext search, and the other handling ICO search. Make sure to use a trigram index to keep the '%%' search fast.

> If you don't want to concatenate the fields repeatedly (it really makes the query harder to read and is error-prone), feel free to create an extra column (with `ts_vector` type) and update the column with the concatenated string. You can now use this "computed" column in your queries.

> You will need to copy&paste the input query into several places in your SQL query. It is OK and don't worry about it. Under "normal" circumstances, the SQL query would be dynamically generated by your application, with the input query interpolated into it.


## Recommended reading
- https://www.postgresql.org/docs/9.4/static/textsearch.html
- https://www.postgresql.org/docs/9.4/static/unaccent.html
- https://www.postgresql.org/docs/9.4/pgtrgm.html

