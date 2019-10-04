#!/bin/bash

echo 'psql -U postgres -h localhost -p 5432 -d shakespeare' | pbcopy;
docker run -p 5432:5432 fiitpdt/postgres-shakespeare;
