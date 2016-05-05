# AWS-Utilities
Collection of scripts for interacting with Amazon Web Services


## download-rds-logs.py
Backup AWS RDS instance logs.

Log files that have already been downloaded will not be re-downloaded.

Options
```
Usage: download-rds-logs.py -i my-instance-id

Options:
  -h, --help            show this help message and exit
  -d, --debug           Turn on debug logging
  -q, --quiet           turn off all logging
  -i INSTANCE, --instance=INSTANCE
                        instance name
  -o OUTPUT_DIR, --output=OUTPUT_DIR
                        output directory
  -r REGION, --region=REGION
                        AWS region
```

Example usage and output: 
```
$ python download-rds-logs.py -i my-instance-id
INFO:root:AdditionalDataPending:True Marker:14:438625
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:438625 chunk:1
INFO:root:AdditionalDataPending:True Marker:14:891049
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:891049 chunk:2
INFO:root:AdditionalDataPending:True Marker:14:1320763
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:1320763 chunk:3
INFO:root:AdditionalDataPending:True Marker:14:1758515
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:1758515 chunk:4
INFO:root:AdditionalDataPending:True Marker:14:2203827
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:2203827 chunk:5
INFO:root:AdditionalDataPending:True Marker:14:2649495
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:2649495 chunk:6
INFO:root:AdditionalDataPending:True Marker:14:3092815
INFO:root:requesting error/postgresql.log.2016-05-04-22 marker:14:3092815 chunk:7
INFO:root:AdditionalDataPending:False Marker:14:3532449
```


## rabbitmq-to-cloudwatch.py
Publish rabbit-mq queue depths as an AWS cloudwatch metric.

Runs as a loop and publishes every 5 minutes.

No command line options.
