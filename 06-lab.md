# Lab 6 - Recursive SQL

Grading: 3pt

## Setup

Download and run the docker container as usual

```
docker run -p 5432:5432 fiitpdt/postgres-recursive
```

> database name: pdt

# Labs

1. Write a recursive query which returns a number and its factorial for all
   numbers up to 10. :coffee:

   ```
      ------------
      | 0  | 1   |
      | 1  | 1   |
      | 2  | 2   |
      | 3  | 6   |
      | 4  | 24  |
      | 5  | 120 |
      ...

   ```

   First we need to decide what is our starting point, for us it was 0 and 1 next we made query which incremented counter and then counted factorial like `other * (n+1)`

   Final Query:
   ```sql
   with recursive fact(n, other) as (
    select 0, 1
    union all
    select n + 1, other * (n+1) from fact
   )
   select n, other from fact limit 10
   ```

2) Write a recursive query which returns a number and the number in Fibonacci
   sequence at that position for the first 20 Fibonacci numbers. :coffee::coffee:

```

      ------------
      | 1  | 1   |
      | 2  | 2   |
      | 3  | 3   |
      | 4  | 5   |
      | 5  | 8   |
      | 6  | 13  |
      | 7  | 21  |
      ...

```
In Fibonacci sequence there are numbers like 1,1,2,3,5,8 so to calculate number we need to make sum 2 numbers before.
We start with values 0,1,0 (counter, value, value_before). In query next value is value + value_before and as we said earlier we need to remember actual value.

Final Query:
```sql

with recursive fib(sa, value, value_before) as (
    select 0,1,0
    union all
    select sa +1 , value + value_before , value  from fib
)
 select sa, value from fib limit 10;

```

3. Table `product_parts` contains products and product parts which are needed to build them. A product part may be used to assemble another product part or product, this is stored in the `part_of_id` column. When this column contains `NULL` it means that it is the final product. List all parts and their components that are needed to build a `'chair'`. :coffee::coffee:

   ```
       ------------
       "armrest"
       "metal leg"
       "metal rod"
       "cushions"
       "red dye"
       "cotton"
       ------------
   ```

   As the starting point we select chair then we recursive iterate to those which are connected with chair via part_of_id it selects next parts and so on.
   
Final Querry:
   ```sql
   with recursive part as (
    select id, name, part_of_id from  product_parts where name = 'chair'
    union
    select pp.id, pp.name, pp.part_of_id from product_parts pp
    join part p on p.id = pp.part_of_id
   )
   select name
   from part where part_of_id is not null;
   ```

4. List all bus stops between 'Zochova' and 'Zoo' for line 39. Also include the hop number on that trip between the two stops. :coffee::coffee:

   ```
       ------------------------------
        name         | hop
       ------------------------------
        Chatam Sófer | 1
        Park kultúry | 2
        Lafranconi   | 3
       ------------------------------
   ```

   We hacked this a little bit we used ZOO as starting point cause we have only one way routes for each line. Then we selected next stop which stating point was the ending point of previous route.

   Final Querry:
   ```sql

      with recursive route(hop, start_stop_id, end_stop_id, name) as (
      select 0, start_stop_id, end_stop_id, stops.name from connections join stops on connections.start_stop_id = stops.id where line = '39' and stops.name = 'Zoo'
      union
      select r.hop + 1, c.start_stop_id, c.end_stop_id, s.name from connections c
        join stops s on c.start_stop_id = s.id
        join route r on r.end_stop_id =  c.start_stop_id
      where line = '39' and r.name != 'Zochova'
      )
      select  * from route;

   ```

## Optional

1. Which one of all the parts that are used to build a `'chair'` has longest shipping time? :coffee::coffee:

   ```
       ------------------------------
        name         | shipping_time
       ------------------------------
        metal rod    | 10
       ------------------------------
   ```

Almost same query as previous chair excercise, but we added shipping time, then ordered it by shipping time and limit 1;

Final Querry:
```sql

with recursive part as (
 select id, name, part_of_id, shipping_time from  product_parts where name = 'chair'
 union
 select pp.id, pp.name, pp.part_of_id, pp.shipping_time from product_parts pp
 join part p on p.id = pp.part_of_id
)
select name, shipping_time
from part where part_of_id is not null order by shipping_time desc limit 1;
```

2. Is it cheaper to order a finished chair from a supplier or is it cheaper if we order the basic components of a chair and build it from scratch? We are only interested in the basic components, e.g., to build a chair we need an armrest, but we do not care about its price since we want to build it from scratch using cotton and red dye. :coffee::coffee::coffee:

   ```
       --------------------------------------
        chair_price_from_basic | chair_price
       --------------------------------------
        14                     | 130
       --------------------------------------
   ```

3. Find line combinations which will get me from 'Nad lúčkami' to 'Zochova' with reasonable transfers between lines. :coffee::coffee::coffee::coffee:

   ```
       ------------------------------
        lines
       ------------------------------
        {9,39}
        {4,39}
        {5,31}
        {4,31}
        {6,39}
        {5,39}
        {9,31}
        {6,31}
        {5,30,31}
        {6,30,31}
        ...
       ------------------------------
   ```

## Recommended reading

- http://www.postgresql.org/docs/8.4/static/queries-with.html
