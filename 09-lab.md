# Session 9 - Elasticsearch

Grading: 4pt

## Setup

```
docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:7.4.2
```

## Labs

### 1. Start by writing the SQL query or queries which will select the data that you want to import to Elasticsearch. Keep in mind that you need to flatten the data, as there are no relations in Elasticsearch. Do the neccessary joins, interesction computations, etc.

We will select all restaurants within districts
The query which used:

```sql
with districts as (
    select name, way from planet_osm_polygon where boundary = 'administrative' and admin_level = '8'
)
select d.name, ARRAY_AGG(distinct pp.name) as restaurants
from planet_osm_point as pp
         cross join districts d
where pp.name is not null pp.amenity = 'restaurant' and st_contains(d.way, pp.way)
group by d.name;

```

### 2. Once you have the data, design the document, e.g., for my example above:

Document will have two attributes - `name` and `restaurants`

```json
{
  "name": "okres Medzilaborce",
  "restaurants": ["Buena", "ESO", "Eurohotel Laborec"]
}
```

### 3. Prepare a mapping, feel free to do it "by hand", e.g. via Postman/curl, you don't need to write code for this.

We used [Insomnia](https://insomnia.io) (alternative of Postman) to create request.
It's simple `PUT` request on endpoint `http://localhost:9200/restaurants` with following body:

```json
{
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "restaurants": {
        "type": "text",
        "fielddata": true
      }
    }
  }
}
```

response:

```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "index": "restaurants"
}
```

### 4. Write a code in a language of your choice which will run the SQL queries, build JSON documents and index them in Elasticsearch. You don't need a library specifically for "Elasticsearch", just use an HTTP client library. Most of the "elasticsearch" libraries that you can find are probably overkill for this lab, as they try to provide ORM functionalities.

### 5. You can always check the data in elasticsearch by running a simple `GET` request at the `_search` endpoint.

Calling `GET` at `http://localhost:9200/_search` endpoint (result is shorten for a reason):

```json
{
  "took": 822,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 80,
      "relation": "eq"
    },
    "max_score": 1.0,
    "hits": [
      {
        "_index": "restaurants",
        "_type": "_doc",
        "_id": "eKu2BG8B4e64ec13d8_B",
        "_score": 1.0,
        "_source": {
          "name": "okres Banská Štiavnica",
          "restaurants": ["6/4", "Adavil", "Erb"]
        }
      },
      {
        "_index": "restaurants",
        "_type": "_doc",
        "_id": "eau2BG8B4e64ec13d8_O",
        "_score": 1.0,
        "_source": {
          "name": "okres Bardejov",
          "restaurants": ["Bocian", "U Bociana"]
        }
      }
    ]
  }
}
```

### 6. Once you have the data, write the Elasticsearch query. It should be really simple, a match query with an aggregation.

We will try simple aggregation to find unique types of restaurants:
Sending `GET` request at `http://localhost:9200/_search` with body:

```json
{
  "size": 0,
  "aggs": {
    "restaurants": {
      "terms": {
        "field": "restaurants"
      }
    }
  }
}
```

result:

```json
{
  "took": 114,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 80,
      "relation": "eq"
    },
    "max_score": null,
    "hits": []
  },
  "aggregations": {
    "restaurants": {
      "doc_count_error_upper_bound": 0,
      "sum_other_doc_count": 4037,
      "buckets": [
        {
          "key": "reštaurácia",
          "doc_count": 60
        },
        {
          "key": "pizzeria",
          "doc_count": 58
        },
        {
          "key": "koliba",
          "doc_count": 31
        }
      ]
    }
  }
}
```

Next we tried to find unique places for district Bratislava

```json
{
  "size": 0,
  "query": {
    "match": {
      "name": "bratislava"
    }
  },
  "aggs": {
    "restaurants": {
      "terms": {
        "field": "restaurants"
      }
    }
  }
}
```

```json
{
  "took": 4,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 5,
      "relation": "eq"
    },
    "max_score": null,
    "hits": []
  },
  "aggregations": {
    "restaurants": {
      "doc_count_error_upper_bound": 0,
      "sum_other_doc_count": 860,
      "buckets": [
        {
          "key": "pizzeria",
          "doc_count": 5
        },
        {
          "key": "reštaurácia",
          "doc_count": 5
        }
        {
          "key": "garden",
          "doc_count": 4
        }
      ]
    }
  }
}
```
