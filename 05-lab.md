# Lab 5 - R-Trees indices, Array and JSON datatypes

Grading: 3pt

## Setup

Download the docker container as usual

```
docker run -p 5432:5432 fiitpdt/postgis
```

You can safely ignore errors about extension being already present and there are some
constraint validation failures, but don't worry about them.

| Attribute                | Value             |
| ------------------------ | ----------------- |
| Login                    | postgres          |
| Database                 | gis               |
| Password                 | none, leave blank |
| Spatial reference system | WGS 84            |

## Labs

1. Write a query which finds all restaurants (point, `amenity = 'restaurant'`) within
   1000 meters of 'Fakulta informatiky a informačných technológií STU'
   (polygon). Select the restaurant name and distance in meters. Sort the
   output by distance - closest restaurant first.

   ```sql
    explain analyse select pop.name, st_distance(p.way::geography, pop.way::geography) as distance from planet_osm_point pop
   join planet_osm_polygon p on st_dwithin(pop.way::geography, p.way::geography, 1000)
   where p.name = 'Fakulta informatiky a informačných technológií STU'
   and pop.amenity = 'restaurant'
   order by distance asc;
   ```

2) Check the query plan and measure how long the query takes. Now make it as
   fast as possible. Make sure to also use geo-indices, but don't expect large
   improvements. The dataset is small, and filtering in `amenity='restaurant'`
   will greatly limit the search space anyway.

Used Query

```sql
create index poly_name_index on planet_osm_polygon(name);
create index poly_amenity_index on planet_osm_polygon(amenity);
create index point_amenity_index on planet_osm_point(amenity);
create index point_name_index on planet_osm_point(name);

create index line_index on
planet_osm_line using gist((way::geography));

create index polygon_index on
planet_osm_polygon using gist((way::geography));

```


> Hint: If you are computing distance from geography for accurate measurement, your index will also need to be created on geography, e.g. `... using gist((way::geography))`. Notice the double parens - they are required, otherwise the parser will be confused by the typecast and throw a syntax error.

#3. Update the query to generate a geojson. The output should be a single row
   containg a json array like this:

```sql

(select row_to_json(r)
 from (
          select pop.name,
                 st_distance(p.way::geography, pop.way::geography) as distance,
                 st_asgeojson(pop.way)::json                       as way
          from planet_osm_point pop
                   join planet_osm_polygon p on st_dwithin(pop.way::geography, p.way::geography, 1000)
          where p.name = 'Fakulta informatiky a informačných technológií STU'
            and pop.amenity = 'restaurant'
          order by distance asc) r);
```

One line

```sql
select json_agg(to_arr)
from (select row_to_json(r) as restaurants
      from (
               select pop.name, st_distance(p.way::geography, pop.way::geography) as distance, st_asgeojson(pop.way)::json
               from planet_osm_point pop
                        join planet_osm_polygon p on st_dwithin(pop.way::geography, p.way::geography, 1000)
               where p.name = 'Fakulta informatiky a informačných technológií STU'
                 and pop.amenity = 'restaurant'
               order by distance asc) r) to_arr;
```

```json
[
{
  "name": "Drag",
  "dist": 99.9,
  "way": {
    "type": "Point",
    "coordinates": [17.07, 48.24]
  }
},
{
  "name": "Koliba",
  "dist": ...
},
...
]
````

Ignore the formatting, the output of your query will not be nicely indented.

> Hint: Use `st_asgeojson` to convert the `way` geometry to JSON. Note that `st_asgeojson` will return the JSON as string, not as a json datatype, so you
will need to cast it to json using `::json`.
You will probably need to use `row_to_json` to convert each row into a json,
`array_agg` to turn all rows into a single row and then `array_to_json` to
convert it back to json.
