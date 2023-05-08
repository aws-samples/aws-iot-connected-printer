# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb')
mqtt_client = boto3.client('iot-data', region_name='us-west-2')
device_inventory_table = os.environ['DEVICE_INVENTORY_TABLE']
job_status_table =ddb.Table(os.environ['JOB_STATUS_TABLE'])
s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))


def write_job_via_mqtt(pyld, mqtt_topic):
    response = mqtt_client.publish(
        topic=mqtt_topic,
        qos=1,
        payload=json.dumps(pyld)
    )

def get_job_status_record(pk):
    data = job_status_table.query(
        KeyConditionExpression=Key('job_id').eq(pk)
    )
    return data['Items'][0]

def create_presigned_url(bucket_name, object_name, expiration=600):
    print(object_name)
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_name
                },
            ExpiresIn=expiration
        )
        
    except Exception as e:
        print(e)
        logging.error(e)
        return "Error"
    # The response contains the presigned URL
    return response

def lambda_handler(event, context):
    print(event)
    if event['Records'][0]['eventName'] == 'ObjectCreated:Put':
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_name = event['Records'][0]['s3']['object']['key']
    
        ## Get the jobs Status Record from Dynamo
        job_id = object_name.split('/')[3].split('-job')[0]
        job_status_record = get_job_status_record(job_id)
        mqtt_topic_name = 'print_jobs/%s' % (
            job_status_record['device_id'],
            
        )

        ## Create a Presigned URL
        presigned_url = create_presigned_url(bucket_name, object_name)

        ## Send the URL to printer via MQTT
        pyld = {
            'job_id':           job_id,
            'presigned_url':    str(presigned_url)
        }
        print(pyld)
        write_job_via_mqtt(pyld, mqtt_topic_name)

        try:
            print("hello")
        except Exception as e:
            print(e)  # TODO add more error handling for job observability

    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
