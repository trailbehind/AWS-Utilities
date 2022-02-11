from botocore import session
import logging
import time
import sys
from datetime import datetime
from datetime import timedelta
from argparse import ArgumentParser

"""
wait-for-stopped-task.py

Given an ECS cluster, a task family name, and an authenticated
AWS environment, this script will wait until the given task 
running on the given cluster has state STOPPED. 

If there are multiple tasks of the same name running on the cluster, 
this script has undefined behavior. Don't use it if that's the case. 

"""


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

parser = ArgumentParser(description=("Wait for ECS task to stop."))
parser.add_argument("--cluster", type=str, required=True)
parser.add_argument("--task-name", type=str, required=True)
parser.add_argument(
    "--max-wait-hours", type=int, default=24, required=False, help="default: 24h"
)
parser.add_argument("--wait-interval-minutes", type=int, default=5, help="default: 5m")

args = parser.parse_args()

botosession = session.Session()
ecs = botosession.create_client("ecs")


# Check (a few times) to see if any task from specified family
# is currently running on specified cluster.
max_retries = 5
retries_remaining = max_retries
task_arn = None
task_params = {
    "cluster": args.cluster,
    "family": args.task_name,
    "desiredStatus": "RUNNING",
}
while retries_remaining:
    logging.info(f"Searching for task {task_params}")
    cluster_running_tasks = ecs.list_tasks(
        cluster=args.cluster, family=args.task_name, desiredStatus="RUNNING"
    )["taskArns"]
    if len(cluster_running_tasks) == 0:
        logger.warning(
            f"No running tasks found. {f'retrying in 60 seconds... ({max_retries - retries_remaining +1 } / {max_retries})'} [task-name: {args.task_name} cluster: {args.cluster}]"
        )
    else:
        if len(cluster_running_tasks) > 1:
            logging.warning("Number of tasks greater than 1! Taking first ARN. ")
        task_arn = cluster_running_tasks[0]
        logging.info(f"Task found. [arn: {cluster_running_tasks[0]}]")
        break

    retries_remaining -= 1
    time.sleep(60)

## Wait for task to enter "STOPPED" state.

start_time = datetime.utcnow()
end_time = start_time + timedelta(hours=args.max_wait_hours)

retries = 0
task_stopped = False
while datetime.utcnow() < end_time or task_stopped:
    task_status = ecs.describe_tasks(cluster=args.cluster, tasks=[task_arn])["tasks"][
        0
    ]["lastStatus"]

    if task_status == "STOPPED":
        logging.info("Task stopped.")
        task_stopped = True
    else:
        logging.info(
            f"Task is still running. Checking again in {args.wait_interval_minutes} minutes."
        )
    time.sleep(args.wait_interval_minutes * 60)

if not task_stopped:
    logging.warning("Stopped task not detected after {args.max_wait_hours}.")
    sys.exit(1)
