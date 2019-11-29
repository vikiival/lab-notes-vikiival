import psycopg2
import json
import requests as req

con = psycopg2.connect(database="slovakia", user="postgres", password="", host="127.0.0.1", port="5432")
cur = con.cursor()

fetch_query = \
    """
    with districts as (
    select name, way from planet_osm_polygon where boundary = 'administrative' and admin_level = '8'
    )
    select d.name, ARRAY_AGG(distinct pp.name) as restaurants
    from planet_osm_point as pp
         cross join districts d
    where pp.name is not null and pp.amenity = 'restaurant' and st_contains(d.way, pp.way)
    group by d.name;
    """

cur.execute(fetch_query)
res = cur.fetchall()

con.close()

processed = list(map(lambda x: { 'name': x[0], 'restaurants': x[1] }, res))
processed_json = json.dumps(processed)

for item in processed:
    req.post('http://localhost:9200/restaurants/_doc', headers={'Content-Type': 'application/json'}, data=json.dumps(item))

