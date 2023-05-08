# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os


ddb = boto3.client('dynamodb')
device_inventory_table = os.environ['DEVICE_INVENTORY_TABLE']
device_telemetry_data = os.environ['DEVICE_TELEMETRY_DATA']

def get_cx():
    data = ddb.scan(
        TableName=device_inventory_table
    )
    return data['Items']

def lambda_handler(event, context):
    # print('request: {}'.format(json.dumps(event)))
    registered_devices = get_cx()
    
    customers = list({x['customer']['S'] for x in registered_devices})
    payload = []

    for c in customers:
        customer_devices = {
            'customer': c
        }

        customer_locations = list({device['location']['S'] for device in registered_devices if device['customer']['S'] == c})
        customer_locations_cont = []

        for loc in customer_locations:
            location = {
                'location': loc
            }
            devices_at_location = []
            for device in registered_devices:
                if (device['location']['S'] == loc and device['customer']['S'] == c):
                    device_at_location = { 'device_id': device['device_id']['S'], 'device_name': device['device_name']['S'] }
                    devices_at_location.append(device_at_location)
            location['devices_at_location'] = devices_at_location
            customer_locations_cont.append(location)
        customer_devices['locations'] = customer_locations_cont
        payload.append(customer_devices)


    return {
        'statusCode': 200,
        'body': json.dumps(payload)
    }

