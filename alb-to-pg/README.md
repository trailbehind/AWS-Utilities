# alb-to-pg
Load ALB logs into a postgres DB for analysis.

Logs can either be loaded directly, or written to CSV, then loaded with postgres `\copy` command. For large logs the csv route is much faster.

## Create table

```
psql --host localhost --user postgres logs -f schema.sql
```

## Directly to postgres

```
gzcat *log*.gz | DB=logs DB_USER=postgres DB_HOST=localhost ./to-csv.py > log.csv
```

## via CSV

format logs as csv
```
gzcat *log*.gz | ./to-csv.py > log.csv
```

Load logs into postgres
```
psql --host localhost --user postgres logs -c "\copy logs FROM 'log.csv' WITH CSV QUOTE '\"'"
```
