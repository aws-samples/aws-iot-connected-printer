# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import datetime
import time

ddb = boto3.client('dynamodb')
device_inventory_table = os.environ['DEVICE_INVENTORY_TABLE']
device_telemetry_data = os.environ['DEVICE_TELEMETRY_DATA']

def get_telemetry(device_id):
    data = ddb.scan(
        TableName=device_telemetry_data
    )

    latest_telemetry = sorted([item['sample_time']['S'] for item in data['Items'] if item['device_id']['S'] == device_id], reverse=True)[0]
    now = time.time()
    date_time = datetime.datetime.fromtimestamp( int(latest_telemetry) ) 
    if now - float(latest_telemetry) > 120:
        return {
            'device_id': device_id,
            'is_available': False,
            'last_seen': latest_telemetry,
            'readable_dt': str(date_time)
        }
    else:
        return {
            'device_id': device_id,
            'is_available': True,
            'last_seen': latest_telemetry,
            'readable_dt': str(date_time)
        }


def lambda_handler(event, context):
    print(event)
    
    device_id = event['device_id']
    
    payload = get_telemetry(device_id)
    

    return {
        'statusCode': 200,
        'body': payload
    }

