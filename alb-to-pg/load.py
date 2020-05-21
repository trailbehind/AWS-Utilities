#!/usr/bin/env python3

import os
import psycopg2
import re
import sys
from urllib.parse import urlparse

try:
    conn = psycopg2.connect(dbname=os.environ.get("DB"), user=os.environ.get("DB_USER"), host=os.environ.get("DB_HOST"))
except Exception as e:
    print("Unable to connect to the database")
    print(e)
    sys.exit(-1)

cur = conn.cursor()
log_pattern = re.compile(r'^(h2|http|https|ws|wss) ([\dT:\-\.]+Z) (\S+) ([\d\.]+:\d+) ([\d\.]+:\d+|-) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (\d\d\d) (\d\d\d|-) (\d+) (\d+) "(\w+) ([\S]+) [^"]+" "([^"]+)" ([\S]+) ([\S]+) ([\S]+) "([^"]+)" "([^"]+)" "([^"]+)"')

loaded_lines = 0
for line in sys.stdin:
    match = log_pattern.match(line)
    if not match:
        print("line does not match: " + line, file=sys.stderr)
        continue
    request_uri = match[14]
    parsed_uri = urlparse(request_uri)

    try:
        cur.execute("INSERT INTO LOGS " +
            "(protocol, response_time, elb_id, client_address, target_address, request_processing_time, target_processing_time, response_processing_time, elb_status_code, target_status_code, received_bytes, sent_bytes, request_method, request_uri_path, request_uri_query, user_agent, ssl_cipher, ssl_protocol, target_group_arn, trace_id, domain_name, chosen_cert_arn)" +
             "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
             (
                match[1], match[2], match[3], match[4], match[5], match[6], match[7], match[8], match[9],
                match[10] if match[10] != "-" else None,
                match[11], match[12], match[13],
                parsed_uri.path[:1024], parsed_uri.query[:1024],
                match[15], match[16], match[17], match[18], match[19], match[20], match[21] 
                ))
    except Exception as e:
        print("error loading line " + line, file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(-1)

    loaded_lines += 1
    if loaded_lines % 10000 == 0:
        print(loaded_lines, file=sys.stderr)
        cur.close()
        conn.commit()
        cur = conn.cursor()
        
cur.close()
conn.commit()

print("Loaded %i lines" % (loaded_lines,), file=sys.stderr)
