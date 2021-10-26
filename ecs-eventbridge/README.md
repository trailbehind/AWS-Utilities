### `send_event.py`

This script sends an event to AWS EventBridge. It has the ability to get JSON metadata from the AWS ECS Metadata Service (or another source) and add that to the body of the event.

To test this script you can run a local Python server (e.g. `python -m http.server 9999` in the `/ecs-eventbridge` directory) and try to post an event like this:

```
awscreds python send_event.py "Wildfire update failed" \
    --metadata --metadata_url "http://localhost:9999/example_ecs_meta.json"
```
By default, the script posts to the default EventBridge bus of the authenticated account in the `us-east-1` region. You can modify these with the `EVENTBRIDGE_BUS_REGION` and `EVENTBRIDGE_BUS_NAME` environment variables.
