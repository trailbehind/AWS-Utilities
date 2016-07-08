#!/usr/bin/env python

import logging
from optparse import OptionParser
import os
from boto import rds2
import sys
import re
import time
import math

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
    parser.add_option("-l", "--lines", action="store", type="int", dest="lines",
        help="Initial number of lines to request per chunk. Number of lines will be reduced if logs get truncated.", default=1000)
    parser.add_option("-b", "--backoff", action="store", type="int", dest="backoff",
        help="Max times to sleep after exponential backoff due to throttling ", default=10)

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
    backoff = options.backoff
    for log in logfiles:
        logging.debug(log)
        logfilename = log['LogFileName']
        lines = options.lines

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
        with open(destination, "wb") as f:
            more_data = True
            marker = "0"
            sleepcount = 0
            while more_data and sleepcount < backoff:
                logging.info("requesting %s marker:%s chunk:%i" % (logfilename, marker, chunk))
                try:
                    response = connection.download_db_log_file_portion(options.instance, logfilename,
                        marker=marker, number_of_lines=lines)
                except:
                    sleeptime=math.pow(2,sleepcount)
                    logging.info("sleep #%s (%s seconds) due to failure" % (sleepcount, sleeptime))
                    time.sleep(sleeptime)
                    sleepcount += 1
                    continue
                sleepcount = 0
                result = response['DownloadDBLogFilePortionResponse']['DownloadDBLogFilePortionResult']
                logging.info("AdditionalDataPending:%s Marker:%s" % (str(result['AdditionalDataPending']), result['Marker']))

                if 'LogFileData' in result and result['LogFileData'] is not None:
                    if result['LogFileData'].endswith("[Your log message was truncated]\n"):
                        logging.info("Log segment was truncated")
                        if lines > options.lines * 0.1:
                            lines -= int(options.lines * 0.1)
                            logging.info("retrying with %i lines" % lines)
                            continue

                    f.write(result['LogFileData'])
                else:
                    logging.error("No LogFileData for file:%s" % (logfilename))

                more_data = 'AdditionalDataPending' in result and result['AdditionalDataPending']
                if 'Marker' in result:
                    marker = result['Marker']
                chunk += 1
                del result['LogFileData']
                logging.debug(result)

            if sleepcount == backoff:
                logging.error("Error downloading file:%s - too many errors from AWS " % (logfilename))


if __name__ == "__main__":
    _main()
