# Session 10 - Elasticsearch

Grading: 2pt

**This is the final lab of this semester**

## Setup

For this lab, you will create a cluster with 6 nodes - 3 data nodes and 3 master-eligible nodes. You could do it by hand, but to save you a lot oftime, you can use a prepared "configuration". To run this configuration, you will need to install docker-compose. Follow the official instructions for your operating system https://docs.docker.com/compose/install/

With docker-compose installed, download docker-compose.yml configuration file from this repository and save it somewhere to your local disk. Change to the directory where you downloaded docker-compose.yml and run

```bash
docker-compose up
```

It will take some time for everything to start, you will see plenty of logging output, but after around a minute, the output should stop and you should be able to run a simple `curl localhost:9200` and get some output.

Note that this lab is very resource intensive. Each elasticsearch instance will **lock** 0.5GB of RAM, and it's quite possible that some nodes will not be able to start. If this happens, try decreasing the number of locked memory by modifying the `ES_JAVA_OPTS` environment inside docker-compose.yml

Remember, that pressing Control + C in the docker-compose window will stop all running docker containers.

**It is ok if you work in groups. If you can't get the cluster running, don't worry about it and a friend who can. Lab notes are still your individual work.**

## Labs

### 1. Check cluster nodes via

```bash
curl -s 'localhost:9200/_cat/nodes?v'
```

Did all nodes join the cluster? Can you tell which node is current master? If you try the command several times, is the master still the same node, or is it changing?

Yes, all nodes joined the cluster. On the snippet below we see that `esmaster03` is master currently.

```
ip         heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
172.18.0.3           40          97   7    1.67    2.13     0.94 ilm       -      esmaster02
172.18.0.5           35          97   7    1.67    2.13     0.94 dil       -      es02
172.18.0.2           41          97   7    1.67    2.13     0.94 dil       -      es01
172.18.0.7           44          97   7    1.67    2.13     0.94 ilm       -      esmaster01
172.18.0.6           34          97   7    1.67    2.13     0.94 dil       -      es03
172.18.0.4           50          97   7    1.67    2.13     0.94 ilm       *      esmaster03

```

### 2. Shut down the current master. For your convenience, the node names are the same as docker container names. To stop a node, simply stop it via docker, e.g.

```
docker stop esmaster01
```
We killed previous master now `esmaster01` is new master.

```
ip         heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
172.18.0.2           30          85   3    0.61    1.74     0.88 dil       -      es01
172.18.0.3           29          85   3    0.61    1.74     0.88 ilm       -      esmaster02
172.18.0.7           38          85   3    0.61    1.74     0.88 ilm       *      esmaster01
172.18.0.6           50          85   3    0.61    1.74     0.88 dil       -      es03
172.18.0.5           51          85   3    0.61    1.74     0.88 dil       -      es02
```

What happened after you stopped the current master? Check `_cat/nodes` again. Did the cluster elect a new master?

What about cluster health? Check `curl 'localhost:9200/_cluster/health?pretty'`. Is the cluster in a green state? Yellow? Or red? Look for "status" in the output json, `grep` is your friend.

```json
{
  "cluster_name" : "es-docker-cluster",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 5,
  "number_of_data_nodes" : 3,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 100.0
}
```

**Optional:** Have a look at the logs in docker-compose output. Can you reconstruct a timeline of events which happened after current master quit?



### 3. While you are at this stage, with 2 masters-eligible nodes, create an index with 2 shards and 1 replica and try indexing some data. It doesn't really matter what you index, just create some index with correct settings and put in a few documents.

```bash
curl -XPUT  "localhost:9200/kiwi" -H 'Content-Type: application/json' -d '
{
    "settings": {
        "index.number_of_shards": 2,
        "index.number_of_replicas": 1
    }
}
'
```
We add data to database like:

```bash
curl -XPOST "localhost:9200/kiwi/airports" -H 'Content-Type: application/json' -d '
{
  "name": "Bratislava",
  "key": "BTS"
}
'
```
result from `GET` at `localhost:9200/kiwi/_search`
```bash
curl 'localhost:9200/kiwi/_search' -H 'Content-Type: application/json'
```

```json
{
  "took": 14,
  "timed_out": false,
  "_shards": {
    "total": 2,
    "successful": 2,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 5,
      "relation": "eq"
    },
    "max_score": 1,
    "hits": [
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "84hmBm8B3WwhCcmgOOpT",
        "_score": 1,
        "_source": {
          "name": "Bratislava",
          "key": "BTS"
        }
      }
    ]
  }
}

```

### 4. Stop another master-eligible node. Just to get a point across - try stopping the master-eligible node that is not currently elected master. Your cluster should now be in a bad state. Try listing all nodes via `_cat/nodes`. Did it work? 

> The qourum is set to 2 so if we kill master node now, new master could not be create. 

```
docker stop esmaster02
```

```bash
curl -s 'localhost:9200/_cat/nodes?v'
```

It causted distruption of the cluster. We got these errors:
```json
{
  "error": {
    "root_cause": [
      {
        "type": "master_not_discovered_exception",
        "reason": null
      }
    ],
    "type": "master_not_discovered_exception",
    "reason": null
  },
  "status": 503
}
```

### 5. In this degraded state, try searching for data. A simple search at the `_search` enpoint is enough, do not bother writing a query. Does searching still work?

We tried `GET` request at `localhost:9200/kiwi/_search`
It worked as usual.

Also for curiosity I tried instert 
```bash
curl -XPOST "localhost:9200/kiwi/airports" -H 'Content-Type: application/json' -d '
     {
       "name": "Brno",
       "key": "BRN"
     }
     '
```

response
```json
{
  "error": {
    "root_cause": [
      {
        "type": "cluster_block_exception",
        "reason": "blocked by: [SERVICE_UNAVAILABLE/2/no master];"
      }
    ],
    "type": "cluster_block_exception",
    "reason": "blocked by: [SERVICE_UNAVAILABLE/2/no master];"
  },
  "status": 503
}
```

### 6. Bring back one of the dead master-eligible nodes

```bash
docker start esmaster02
```

The node became avaible in the couple of minutes and we were able to show list of nodes again which was not working with only one master-egible node.

### 7. Inspect your shard layout via

```bash
curl localhost:9200/_cat/shards
```

```
kiwi 1 p STARTED 3 4.4kb 172.18.0.5 es02
kiwi 1 r STARTED 3 4.4kb 172.18.0.2 es01
kiwi 0 p STARTED 2 4.2kb 172.18.0.6 es03
kiwi 0 r STARTED 2 4.2kb 172.18.0.2 es01
```

Select a node which has some shards and stop it.

We killer `es02`

```
kiwi 1 p STARTED    3 4.4kb 172.18.0.2 es01
kiwi 1 r UNASSIGNED
kiwi 0 p STARTED    2 4.2kb 172.18.0.6 es03
kiwi 0 r STARTED    2 4.2kb 172.18.0.2 es01
```

> Inspect the shard layout again. Note that if you stoped node `es01`, your port 9200 is now dead too. Try port 9201 (es02) or 9202 (es03). Note that these port mapping are set up specifically for this lab, under normal circumstances each node runs on 9200 on its own host.


What is the cluster health now? Also check index-level healt by running

```
curl localhost:9200/_cat/indices
```
```bash
yellow open kiwi 2J3u__T9QNyAEI7OypsrEQ 2 1 5 0 12.9kb 8.7kb
```

### 8. Take down another node and repeat tasks from 7. Again, keep in mind that by stopping a host, you may have cut off your access via the port you were using. In that case, try using a different port (9200, 9201, 9202)

We stopped `es03` now
```
docker stop es03
```

```
curl localhost:9200/_cat/shards
```

Now running shards
```
kiwi 1 p STARTED    3 4.4kb 172.18.0.2 es01
kiwi 1 r UNASSIGNED
kiwi 0 p STARTED    2 4.2kb 172.18.0.2 es01
kiwi 0 r UNASSIGNED
```
```bash
curl -s 'localhost:9200/_cat/nodes?v'
```
```
ip         heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
172.18.0.3           35          71   2    0.34    0.28     0.34 ilm       *      esmaster02
172.18.0.2           32          71   2    0.34    0.28     0.34 dil       -      es01
172.18.0.7           35          71   2    0.34    0.28     0.34 ilm       -      esmaster01
```

### 9. Try searching and indexing in this state. Are both operations working?
We had to use 
```bash
curl 'http://localhost:9201/kiwi/_search'
```
because we killed `es01` node

Searching and indexing works correctly.

### 10. Take down the last data node. Access the cluster via master node, via port 9210, 9211 or 9212. What is cluster health now? Index-level health? Shard allocation?
```bash
curl -s 'localhost:9211/_cat/nodes?v'
```
```
ip         heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
172.18.0.3           45          46   1    0.01    0.07     0.19 ilm       *      esmaster02
172.18.0.7           44          46   1    0.01    0.07     0.19 ilm       -      esmaster01
```

The health of actual cluster
```bash
curl localhost:9210/_cat/indices
red open kiwi 2J3u__T9QNyAEI7OypsrEQ 2 1
```

```
curl localhost:9210/_cat/shards
```

```
kiwi 1 p UNASSIGNED
kiwi 1 r UNASSIGNED
kiwi 0 p UNASSIGNED
kiwi 0 r UNASSIGNED
```

### 11. Bring back the data nodes one by one and observe what happens. Did you lose any data when all 3 data nodes went down?

```
docker start es01 es02 es03
```

```bash
curl 'http://localhost:9201/kiwi/_search'
```

Results
``` json
{
  "took": 26,
  "timed_out": false,
  "_shards": {
    "total": 2,
    "successful": 2,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 6,
      "relation": "eq"
    },
    "max_score": 1,
    "hits": [
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "9IhmBm8B3WwhCcmggepf",
        "_score": 1,
        "_source": {
          "name": "Los Angeles",
          "key": "LAX"
        }
      },
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "9YhmBm8B3WwhCcmg_Op5",
        "_score": 1,
        "_source": {
          "name": "Vienna",
          "key": "VIE"
        }
      },
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "WDODBm8B6zbI8nsHWdYG",
        "_score": 1,
        "_source": {
          "name": "Budapest",
          "key": "BUD"
        }
      },
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "84hmBm8B3WwhCcmgOOpT",
        "_score": 1,
        "_source": {
          "name": "Bratislava",
          "key": "BTS"
        }
      },
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "9ohnBm8B3WwhCcmgM-ru",
        "_score": 1,
        "_source": {
          "name": "Prague",
          "key": "PRG"
        }
      },
      {
        "_index": "kiwi",
        "_type": "airports",
        "_id": "94hnBm8B3WwhCcmgyOo7",
        "_score": 1,
        "_source": {
          "name": "Berlin Schonefeld",
          "key": "SFX"
        }
      }
    ]
  }
}
```

I'm just missing Brno.

```
curl localhost:9210/_cat/shards
kiwi 1 r STARTED 3 4.4kb 172.18.0.4 es02
kiwi 1 p STARTED 3 4.4kb 172.18.0.2 es01
kiwi 0 r STARTED 3 8.1kb 172.18.0.5 es03
kiwi 0 p STARTED 3 8.1kb 172.18.0.4 es02
```