#!/usr/bin/env python3

import os
import re
import sys
import csv
from urllib.parse import urlparse

log_pattern = re.compile(r'^(h2|http|https|ws|wss) ([\dT:\-\.]+Z) (\S+) ([\d\.]+:\d+) ([\d\.]+:\d+|-) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (\d\d\d) (\d\d\d|-) (\d+) (\d+) "(\w+) ([\S]+) [^"]+" "([^"]+)" ([\S]+) ([\S]+) ([\S]+) "([^"]+)" "([^"]+)" "([^"]+)"')

writer = csv.writer(sys.stdout, delimiter=',', quotechar="\"", quoting=csv.QUOTE_MINIMAL)
loaded_lines = 0
for line in sys.stdin:
    match = log_pattern.match(line)
    if not match:
        print("line does not match: " + line, file=sys.stderr)
        continue
    request_uri = match[14]
    parsed_uri = urlparse(request_uri)

    writer.writerow(
        [match[1], match[2], match[3], match[4], match[5], match[6], match[7], match[8], match[9] or "",
        match[10] if match[10] != "-" else "",
        match[11], match[12], match[13],
        parsed_uri.path[:1024], parsed_uri.query[:1024],
        match[15], match[16], match[17], match[18], match[19], match[20], match[21]]
    )
    loaded_lines += 1
    if loaded_lines % 10000 == 0:
        print(loaded_lines, file=sys.stderr)

print("Loaded %i lines" % (loaded_lines,), file=sys.stderr)
