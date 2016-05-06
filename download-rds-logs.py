#!/usr/bin/env python

import logging
from optparse import OptionParser
import os
from boto import rds2
import sys
import re

AWS_REGIONS = ["us-east-1", "us-west-1", "us-west-2", "eu-west-1", \
    "eu-central-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",\
    "sa-east-1"]

def _main():
    usage = "usage: %prog -i my-instance-id"
    parser = OptionParser(usage=usage,
                          description="")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Turn on debug logging")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                      help="turn off all logging")
    parser.add_option("-i", "--instance", action="store", dest="instance",
                      default=None,
                      help="instance name")
    parser.add_option("-o", "--output", action="store", dest="output_dir",
                      default="./",
                      help="output directory")
    parser.add_option("-r", "--region", action="store", dest="region",
        default="us-east-1",
        choices=AWS_REGIONS,
        help="AWS region")
    parser.add_option("-m", "--match", action="store", dest="logfile_match",
        help="Only download logs matching regexp")

    (options, args) = parser.parse_args()
 
    logging.basicConfig(level=logging.DEBUG if options.debug else
    (logging.ERROR if options.quiet else logging.INFO))

    if not options.instance:
        logging.error("Instance parameter is required")
        sys.exit(-1)

    if not os.path.exists(options.output_dir):
        os.mkdir(options.output_dir)

    connection = rds2.connect_to_region(options.region)
    response = connection.describe_db_log_files(options.instance)
    logfiles = response['DescribeDBLogFilesResponse']['DescribeDBLogFilesResult']['DescribeDBLogFiles']
    for log in logfiles:
        logging.debug(log)
        logfilename = log['LogFileName']

        if options.logfile_match is not None and not re.search(options.logfile_match, logfilename):
            logging.info("Skipping " + logfilename)
            continue

        destination = os.path.join(options.output_dir, os.path.basename(logfilename))

        if os.path.exists(destination):
            statinfo = os.stat(destination)
            if statinfo.st_size == log['Size']:
                logging.info("File %s exists, skipping" % (logfilename))
                continue
            else:
                logging.info("Log file %s exists, but size does not match, redownloading." % (logfilename))
                logging.info("Local files size %d expected size:%d" % (statinfo.st_size, log['Size']))
                os.remove(destination)

        chunk = 0
        with open(destination, "w") as f:
            more_data = True
            marker = "0"
            while more_data:
                logging.info("requesting %s marker:%s chunk:%i" % (logfilename, marker, chunk))
                response = connection.download_db_log_file_portion(options.instance, logfilename,
                    marker=marker)
                result = response['DownloadDBLogFilePortionResponse']['DownloadDBLogFilePortionResult']
                logging.info("AdditionalDataPending:%s Marker:%s" % (str(result['AdditionalDataPending']), result['Marker']))
                logging.debug(result)
                if 'LogFileData' in result and result['LogFileData'] is not None:
                    f.write(result['LogFileData'])
                else:
                    logging.error("No LogFileData for file:%s" % (logfilename))
                more_data = 'AdditionalDataPending' in result and result['AdditionalDataPending']
                if 'Marker' in result:
                    marker = result['Marker']
                chunk += 1

if __name__ == "__main__":
    _main()
