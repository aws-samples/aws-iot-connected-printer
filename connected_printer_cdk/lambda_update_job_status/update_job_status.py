# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
job_status_table = ddb.Table(os.environ['JOB_STATUS_TABLE'])

def get_job_status_record(pk):
    data = job_status_table.query(
        KeyConditionExpression=Key('job_id').eq(pk)
    )
    return data['Items'][0]

def lambda_handler(event, context):
    print(event)
    
    now = datetime.now()

    try: 
        ## get job status record from dynamodb
        job_status_record = get_job_status_record(event['job_id'])

        print(job_status_record)

        job_status_record['status'] = event['status']
        job_status_record['last_modified'] = event['timestamp']
        
        if(job_status_record['status'] == 'Succeeded'):
            job_status_record['succeeded_at'] = event['timestamp']
        if(job_status_record['status'] == 'Failed'):
            job_status_record['exception'] = event['exception']

        pyld = job_status_record

        ## Upsert record of job to job_status_table
        job_status_table.put_item(Item=pyld)
    except Exception as e:
        print(e) ## TODO add better error handling for job observability

    return {
        'statusCode': 200,
        'body': json.dumps({
            "Message": "Print Job Successfully Updated"
        })
    }
