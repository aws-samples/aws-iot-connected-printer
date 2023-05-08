# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os
from datetime import datetime
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

ddb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
device_inventory_table = ddb.Table(os.environ['DEVICE_INVENTORY_TABLE'])
job_status_table = ddb.Table(os.environ['JOB_STATUS_TABLE'])
print_job_bucket = os.environ['PRINT_JOB_BUCKET']

def get_card_design(card_design, cardholder, filename):
    print('/card_designs/'+card_design)
    s3_client.download_file(print_job_bucket,'card_designs/'+card_design, '/tmp/blank_card.png')
    img = PIL.Image.open('/tmp/blank_card.png')
    d1 = PIL.ImageDraw.Draw(img)
    font = PIL.ImageFont.truetype('Amazon-Ember-Medium.ttf', size=44)
    d1.text((600, 516), cardholder, font=font, fill=(0, 0, 0))
    img.save("/tmp/"+filename+".png")

def lambda_handler(event, context):
    print(event)

    now = datetime.now()
    
    pyld = {
        'job_id':           event['job_id'],
        'created_at':       str(now),
        'customer':         event['customer'],
        'location':         event['location'],
        'device':           event['device_name'],
        'device_id':        event['device_id'],
        'first_name':       event['firstName'],
        'last_name':        event['lastName'],
        'card_design':      event['card_design'],
        'status':           'Created',
        'exception':        None,
        'last_modified':    None,
        'succeeded_at':     None
    }

    key = now.strftime('%Y/%m/%d/') + pyld['job_id'] + '-job.png'

    pyld['print_job_file'] = 's3://'+print_job_bucket+'/'+key
    cardholder = '%s %s' % (event['firstName'], event['lastName'])
    get_card_design(event['card_design'], cardholder, pyld['job_id'])

    try: 
        ## upload local print job file to s3
        print_response = s3_client.upload_file('/tmp/'+pyld['job_id']+'.png', print_job_bucket, key)

        ## write record of job to job_status_table
        job_status_table.put_item(Item=pyld)
    except Exception as e:
        print(e)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "Message": "Print Job Successfully Created"
        })
    }
