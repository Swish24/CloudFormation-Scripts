import json
import urllib3
import os
from datetime import datetime

print(os.environ['webhookType'])
site = os.environ['webhookType']

print(os.environ['webhookUrl'])
webhookUrl = os.environ['webhookUrl']
http = urllib3.PoolManager()


# Create our discord alert function
def sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName):
    eventTime_str = datetime.strptime(eventTime, "%Y-%m-%dT%H:%M:%S.%fZ")
    unix_timestamp = int(eventTime_str.timestamp())
    if site == 'Slack':
      webhook = webhookUrl
      embedData = {
    "attachments": [
        {
            "color": color,
            "title": eventName,
            "fields": [
                {
                    "title": "Bucket Name",
                    "value": s3BucketName,
                    "short": "false"
                },
                {
                    "title": "Object Name",
                    "value": objectName,
                    "short": "false"
                },
                {
                    "title": "IP Address",
                    "value": sourceIPAddress,
                    "short": "false"
                },
                {
                    "title": "timestamp",
                    "value": eventTime,
                    "short": "false"
            },
            ],
        }
    ]
}
      json_payload = json.dumps(embedData).encode('utf-8')
    elif site == 'Discord':
      webhook = webhookUrl
      embedData = {
          "title": eventName,
          "color": color,
          "fields": [
              {
                  "name": "Event Time",
                  "value": f"<t:{unix_timestamp}>",
              },
              {
                  "name": "IP Address",
                  "value": sourceIPAddress,
              },
              {
                  "name" : "Bucket Name",
                  "value": s3BucketName,
              },
              {
                  "name": "Object Name",
                  "value": objectName,
              },
          ],
          "footer": {
              "text": "Lambda S3 Monitor"
          },
          "timestamp": eventTime
      }
      json_payload = json.dumps({'embeds': [embedData]}).encode('utf-8')
    elif site == 'Custom':
      webhook = webhookUrl
      embedData = {
          "EventName": eventName,
          "EventTime": eventTime,
          "IPAddress": sourceIPAddress,
          "BucketName": s3BucketName,
          "ObjectName": objectName,
          "color": color
          }
      json_payload = json.dumps(embedData).encode('utf-8') 
    req = http.request(
      'POST',
      webhook,
      body=json_payload,
      headers={'Content-Type': 'application/json'} 
    )
  # Check response of the POST request to discord, 204 is expected per the Discord docs, 4xx, 5xx is a failure
    if req.status == 200 or 204:
      return True
    elif req.status == 400:
      return False
    
def lambda_handler(event, context):

  record = (event['Records'][0]['body'])
  # Parse the Event data to JSON, so we can pass it through to our alert function
  parsed = json.loads(record)

  if 'Event' not in parsed:
    eventName = (parsed['Records'][0]['eventName'])
    eventTime = (parsed['Records'][0]['eventTime'])
    sourceIPAddress = (parsed['Records'][0]['requestParameters']['sourceIPAddress'])
    s3BucketName = (parsed['Records'][0]['s3']['bucket']['name'])
    objectName = (parsed['Records'][0]['s3']['object']['key'])
    # print(eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
    # Check for whnich event occured, this will allow us to put specific colors on our webhook to Discord/Slack
    def event_name(site, eventName, eventTime, sourceIPAddress, s3BucketName, objectName):
      match eventName:
        case 'ObjectCreated:Put':
              if site == 'Slack':
                color = '#1ABC9C'
                alert = sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
              elif site =='Discord':
                color = 1752220
                alert = sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
              elif site =='Custom':
                color = '#1ABC9C'
                alert = sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
              if alert:
                  return True
              else:
                  return False
        case 'ObjectRemoved:Delete':
              if site == 'Slack':
                color = '#992D22'
                alert = sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
              elif site =='Discord':
                color = 10038562
                alert = sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
              elif site =='Custom':
                color = '#992D22'
                alert = sendAlert(site, color, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
              if alert:
                  return True
              else:
                  return False
        case _:
              return "Unrecognized event received"

    request = event_name(site, eventName, eventTime, sourceIPAddress, s3BucketName, objectName)
  #Return success or failure from lambda Response, this will tell the SQS queue to stop on success or try again on failure
    if request:
      return True
    else: 
      return False
  else:
    print('SQS Test Message received, ignoring')