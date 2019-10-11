# Lab 3 - PostGIS

Grading: 3pt

## Setup

Download the docker container as usual

````
docker run -p 5432:5432 fiitpdt/postgis
````

You can safely ignore errors about extension being already present and there are some
constraint validation failures, but don't worry about them.

| Attribute| Value                  |
|----------|------------------------|
| Login    | postgres               |
| Database | gis                    |
| Password | none, leave blank      |
| Spatial reference system | WGS 84 |


## 1. How far (air distance) is FIIT STU from the Bratislava main train station?
   The query should output the distance in meters without any further
   modification.

  ```sql
  with fiit as (
    select name, way from planet_osm_polygon
    where name = 'Fakulta informatiky a informačných technológií STU'
)

select st_distance(fiit.way::geography, poly.way::geography) from planet_osm_polygon poly
    cross join fiit
    where poly.name = 'Hlavná stanica Bratislava'
;
```

   *Hint: notice the difference between geometry and geography types in this
   case.*

## 2. Which other districts are direct neighbours with 'Karlova Ves'?

```sql
with district as (
    select * from planet_osm_polygon poly
    where poly.boundary = 'administrative'
    and poly.admin_level = '9'
)

select d.name from planet_osm_polygon poly
cross join district d
where poly.name = 'Karlova Ves'
and poly.admin_level = '9'
and st_touches(d.way, poly.way)
```

## 3. Which bridges cross over the Danube river?

```sql
with dunaj as (
    (select * from planet_osm_polygon where name = 'Dunaj')
    union
    (select * from planet_osm_line where name = 'Dunaj')
)

select distinct p.name from planet_osm_line p
cross join dunaj
where p.bridge = 'yes' and p.name is not null
```

## 4. Find the names of all streets in 'Dlhé diely' district.


```sql

with dlhe_diely as (
    select * from planet_osm_polygon
    where name = 'Dlhé diely'
)

select distinct street.name from planet_osm_line street
cross join dlhe_diely
where street.highway = 'residential'
and st_contains(dlhe_diely.way, street.way)

```

Optional:

## 5. What percentage of area of 'Dlhé diely' is available for leisure? (such as parks, tennis courts, etc.)

## 6. In which restaurants can you enjoy a view of the Danube river? Let's say that the air distance must be less than 300 meters.

  *Hint: The Danube river is composed of multiple lines and polygons*

### Cross joins

You'll be using cross joins (cartesian joins) a lot, because often, there is
no column to join on. The regular join syntax requires an `ON` clausule, so
something like the following is a syntax error:
````
SELECT * FROM planet_osm_line l
  JOIN planet_osm_polygon p 
 WHERE p.name = 'Karlova Ves'
````
Instead, you need to do
````
SELECT * FROM planet_osm_line l 
 CROSS JOIN planet_osm_polygon p
 WHERE p.name = 'Karlova Ves'
````

### `WITH` clausule

When you need to use a subselect, the query can often get very hairy and
unreadable. Alternatively, you can first set up all subqueries and then just
reference them, e.g.:

````
WITH leisure AS (
  SELECT * FROM planet_osm_polygon p
  WHERE leisure IS NOT NULL
)
SELECT SUM(st_area(way)) FROM leisure
````