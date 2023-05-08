# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import datetime

ddb = boto3.resource('dynamodb')
device_inventory_table = ddb.Table(os.environ['DEVICE_INVENTORY_TABLE'])


def lambda_handler(event, context):

    device_inventory_record = {
        'device_id': event['parameters']['DeviceID'],
        'device_name': event['parameters']['DeviceName'],
        'customer': event['parameters']['Customer'],
        'location': event['parameters']['Location'],
        'provisioned_at': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    ## record device attributes in inventory table
    device_inventory_table.put_item(Item=device_inventory_record)

    return {
        'allowProvisioning': True
    }

