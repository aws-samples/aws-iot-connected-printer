# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt
import sys
import threading
import time
from uuid import uuid4
import json
import os
import requests
import datetime
import time
from urllib.parse import unquote
import subprocess

# This sample uses the Message Broker for AWS IoT to send and receive messages
# through an MQTT connection. On startup, the device connects to the server,
# subscribes to a topic, and begins publishing messages to that topic.
# The device should receive those same messages back from the message broker,
# since it is subscribed to that same topic.

# Parse arguments
import command_line_utils;
cmdUtils = command_line_utils.CommandLineUtils("PubSub - Send and recieve messages through an MQTT connection.")
cmdUtils.add_common_mqtt_commands()
cmdUtils.add_common_topic_message_commands()
cmdUtils.add_common_proxy_commands()
cmdUtils.add_common_logging_commands()
cmdUtils.register_command("key", "<path>", "Path to your key in PEM format.", True, str)
cmdUtils.register_command("cert", "<path>", "Path to your client certificate in PEM format.", True, str)
cmdUtils.register_command("device_id", "<uuid, Str>", "id of this device, set upon provisioning", True, str)
cmdUtils.register_command("device_name", "<uuid, Str>", "name of this device, set upon provisioning", True, str)
cmdUtils.register_command("port", "<int>", "Connection port. AWS IoT supports 443 and 8883 (optional, default=auto).", type=int)
cmdUtils.register_command("client_id", "<str>", "Client ID to use for MQTT connection (optional, default='test-*').", default="test-" + str(uuid4()))
cmdUtils.register_command("count", "<int>", "The number of messages to send (optional, default='10').", default=0, type=int)
cmdUtils.register_command("is_ci", "<str>", "If present the sample will run in CI mode (optional, default='None')")
# Needs to be called so the command utils parse the commands
cmdUtils.get_args()

received_count = 0
received_all_event = threading.Event()
is_ci = cmdUtils.get_command("is_ci", None) != None
device_id = cmdUtils.get_command("device_id", None)
device_name = cmdUtils.get_command("device_name", None)

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))

def publish_mqtt_message(mqtt_connection, topic, pyld):
    # pyld = "{}".format(message_string)
    # print("Publishing message to topic '{}': {}".format(topic, message_string))
    print('topic being published to:')
    print(topic)
    message_json = json.dumps(pyld)
    print(str(pyld))
    mqtt_connection.publish(
        topic=topic,
        payload=message_json,
        qos=mqtt.QoS.AT_LEAST_ONCE
    )

# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):

    new_payload = json.loads(payload.decode('utf-8'))
    job_id = new_payload['job_id']

    presigned_url = new_payload['presigned_url']
    
    response = requests.get(presigned_url)

    file_name = "/home/pi/files/%s-job.png" % (job_id)

    print(file_name)
    file_content = response.content


    with open(file_name, 'wb') as file_o:
        file_o.write(file_content)
    time.sleep(3)
    command = "lp -d HPLJ -o media=a4 -o sides=one-sided %s" % (file_name)
    print('running command w Popen:')
    print(command)

    job_status_topic = 'job_status/%s/%s' % (device_id, job_id)
    now = time.time()
    dt = datetime.datetime.fromtimestamp(now)
    job_status_message = {
        'device_id': device_id,
        'job_id': job_id,
        'timestamp': str(dt)
    }
    try:
        result = subprocess.Popen(command, shell=True)
        result_text = result.communicate()[0]
        print(result_text)
        
        return_code = result.returncode
        print(return_code)

        if return_code == 1:
            print("PrintCommand Failed with: %s" % (result_text))
            ## write error to mqtt
            job_status_message['status'] = 'Failed'
            job_status_message['exception'] = result_text
            publish_mqtt_message(mqtt_connection, job_status_topic, job_status_message)
        else:
            ## write success to mqtt
            print("Print Succeeded")
            job_status_message['status'] = 'Succeeded'
            # job_status_message['exception'] = result_text
            publish_mqtt_message(mqtt_connection, job_status_topic, job_status_message)
    except Exception as e:
        print(e)
        job_status_message['status'] = 'Failed'
        job_status_message['exception'] = e
        publish_mqtt_message(mqtt_connection, job_status_topic, job_status_message)

    global received_count
    received_count += 1
    if received_count == cmdUtils.get_command("count"):
        received_all_event.set()

if __name__ == '__main__':
    mqtt_connection = cmdUtils.build_mqtt_connection(on_connection_interrupted, on_connection_resumed)

    if is_ci == False:
        print("Connecting to {} with client ID '{}'...".format(
            cmdUtils.get_command(cmdUtils.m_cmd_endpoint), cmdUtils.get_command("client_id")))
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_count = cmdUtils.get_command("count")
    print_job_topic = 'print_jobs/%s' % (device_id)
    printer_status_topic = 'printer_status/%s' % (device_id)
    message_string = {
        'device_id': device_id,
        'printer_name': device_name,
        'accepting_jobs': True
    }

    # Subscribe
    print("Subscribing to topic '{}'...".format(print_job_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=print_job_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    # Publish message to server desired number of times.
    # This step is skipped if message is blank.
    # This step loops forever if count was set to 0.
    if message_string:
        if message_count == 0:
            print ("Sending messages until program killed")
        else:
            print ("Sending {} message(s)".format(message_count))

        publish_count = 1
        while (publish_count <= message_count) or (message_count == 0):
            now = time.time()
            dt = datetime.datetime.fromtimestamp(now)
            ttl = dt + datetime.timedelta(minutes=30)
            message_string['sample_time'] = str(now).split('.')[0]
            message_string['ttl'] = ttl.timestamp()
            message = "{}".format(message_string)
            print("Publishing message to topic '{}': {}".format(printer_status_topic, message))
            message_json = json.dumps(message_string)
            mqtt_connection.publish(
                topic=printer_status_topic,
                payload=message_json,
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            time.sleep(30)
            publish_count += 1

    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect


    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
