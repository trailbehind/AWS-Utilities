# Assorted AWS lambda functions

## cloudwatch-alarm-to-slack
Post cloudwatch alarms to a slack channel. Reads alarms from SQS.

Based on example template from AWS, but has nicer formatting of slack messages.

Uses KMS to decrypt slack webhook url.

