import argparse
from subprocess import check_output, CalledProcessError
from urllib.request import urlopen
from urllib.error import URLError
from os import environ
import json
from tempfile import TemporaryFile

EVENTBRIDGE_BUS_REGION = environ.get('EVENTBRIDGE_BUS_REGION', 'us-east-1')
EVENTBRIDGE_BUS_NAME = environ.get('EVENTBRIDGE_BUS_NAME', None)
AWS_PUT_EVENTS = "aws --region {EVENTBRIDGE_BUS_REGION} events put-events --entries '{json_events}'"


parser = argparse.ArgumentParser(description="Post EventBridge event.")
parser.add_argument("event_text")
parser.add_argument("--error", help="Flag for error event.", action='store_true')
parser.add_argument("--success", help="Flag for success event.", action='store_true')
parser.add_argument("--info", help="Flag for info event.", action='store_true'),
parser.add_argument("--source", help="Specify source of event (e.g. pipeline/software/tool/etc).")
parser.add_argument("--eventbridge_source", help="EventBridge source. (Default: \"gaiagps.maps\"", default="gaiagps.maps")
parser.add_argument(
    "--metadata", help="Send JSON metadata from Metadata Service (change url with --metadata_url) along with event.",
    action="store_true"
)
parser.add_argument(
    "--metadata_url", 
    help="URL to server hosting JSON metadata (e.g. from the AWS Metadata Service) to append to the event. (Default: ${ECS_CONTAINER_METADATA_URI_V4})"
)

args = parser.parse_args()

METADATA_URL = args.metadata_url if args.metadata_url else environ.get("ECS_CONTAINER_METADATA_URI_V4", "") + '/task'

metadata = None
if args.metadata and METADATA_URL:
    try: 
        metadata = json.loads(urlopen(METADATA_URL).read())
    except Exception as e:
        print(f"Can't open metadata url. [url: {METADATA_URL}]")
        metadata = None

event_type = None
if args.error:
    event_type = 'error'
if args.success: 
    event_type = 'success'
if args.info: 
    event_type = 'info'

event_source = None
if args.source:
    event_source = args.source


event = {
    'DetailType': args.event_text,
    'Source': args.eventbridge_source,
    'Detail': "{}"
}
if EVENTBRIDGE_BUS_NAME:
    event.update({'EventBusName': EVENTBRIDGE_BUS_NAME})

_event_meta = {
    'Event_type': event_type,
    'Event_source': event_source
}

if metadata:
    metadata.update(_event_meta)
    event.update({'Detail': json.dumps(metadata)})
elif event_type:
    event.update({
        'Detail' : json.dumps(_event_meta)
    })

# test for credentials
hasCreds = True
try: 
    credsCheck = check_output("aws sts get-caller-identity", shell=True)
except CalledProcessError:
    hasCreds=False



cmd = AWS_PUT_EVENTS.format(
    json_events = json.dumps([event]),
    EVENTBRIDGE_BUS_REGION = EVENTBRIDGE_BUS_REGION
)
if hasCreds:
    check_output(cmd, shell=True)
else:
    print("No AWS credentials found. Printing command below:")
    print(cmd)

