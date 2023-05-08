# registering the thing with Fleet Provisioning by Claim

aws iam create-role --role-name FleetProvisioningRole --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Effect":"Allow","Principal":{"Service":"iot.amazonaws.com"}}]}'

aws iam attach-role-policy \
        --role-name FleetProvisioningRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTThingsRegistration

aws iot create-provisioning-template \
        --template-name PrinterTemplate \
        --provisioning-role-arn arn:aws:iam::933617207381:role/FleetProvisioningRole \
        --template-body '{ "Parameters": { "Customer": { "Type": "String" }, "AWS::IoT::Certificate::Id": { "Type": "String" }, "DeviceID": { "Type": "String" } }, "Mappings": { "CustomerTable": { "MBAWS": { "CustomerUrl": "https://example.aws" } } }, "Resources": { "thing": { "Type": "AWS::IoT::Thing", "Properties": { "ThingName": { "Fn::Join": [ "", [ "DeviceID_", { "Ref": "DeviceID" } ] ] }, "AttributePayload": { "version": "v1", "deviceID": "deviceID" } }, "OverrideSettings": { "AttributePayload": "MERGE", "ThingTypeName": "REPLACE", "ThingGroups": "DO_NOTHING" } }, "certificate": { "Type": "AWS::IoT::Certificate", "Properties": { "CertificateId": { "Ref": "AWS::IoT::Certificate::Id" }, "Status": "Active" }, "OverrideSettings": { "Status": "REPLACE" } }, "policy": { "Type": "AWS::IoT::Policy", "Properties": { "PolicyDocument": { "Version": "2012-10-17", "Statement": [ { "Effect": "Allow", "Action": [ "iot:Connect", "iot:Subscribe", "iot:Publish", "iot:Receive" ], "Resource": "*" } ] } } } } }' \
        --enabled

'{ "Parameters": { "Customer": { "Type": "String" }, "AWS::IoT::Certificate::Id": { "Type": "String" }, "DeviceID": { "Type": "String" } }, "Mappings": { "CustomerTable": { "MBAWS": { "CustomerUrl": "https://example.aws" } } }, "Resources": { "thing": { "Type": "AWS::IoT::Thing", "Properties": { "ThingName": { "Fn::Join": [ "", [ "DeviceID", { "Ref": "DeviceID" } ] ] }, "AttributePayload": { "version": "v1", "deviceID": "deviceID" } }, "OverrideSettings": { "AttributePayload": "MERGE", "ThingTypeName": "REPLACE", "ThingGroups": "DO_NOTHING" } }, "certificate": { "Type": "AWS::IoT::Certificate", "Properties": { "CertificateId": { "Ref": "AWS::IoT::Certificate::Id" }, "Status": "Active" }, "OverrideSettings": { "Status": "REPLACE" } }, "policy": { "Type": "AWS::IoT::Policy", "Properties": { "PolicyDocument": { "Version": "2012-10-17", "Statement": [ { "Effect": "Allow", "Action": [ "iot:Connect", "iot:Subscribe", "iot:Publish", "iot:Receive" ], "Resource": "*" } ] } } } } }'

aws iot delete-provisioning-template --template-name PrinterTemplate

{
    "templateArn": "arn:aws:iot:us-west-2:933617207381:provisioningtemplate/PrinterTemplate",
    "templateName": "PrinterTemplate",
    "defaultVersionId": 1
}

aws iot create-provisioning-claim \
        --template-name PrinterTemplate \
        | python3 ../utils/parse_cert_set_result.py \
        --path /tmp \
        --filename provision
       
python fleetprovisioning.py \
        --endpoint am6j7nlhi3tht-ats.iot.us-west-2.amazonaws.com \
        --ca_file /home/pi/.ssh/AmazonRootCA1.pem \
        --cert /tmp/provision.cert.pem \
        --key /tmp/provision.private.key \
        --template_name PrinterTemplate \
        --template_parameters "{\"Customer\":\"MBAWS\",\"DeviceID\":\"HPLJ_MFP_M428FDW\"}"

get amazonCA cert - https://www.amazontrust.com/repository/AmazonRootCA1.pem


#--------- getting printer to work -------------------

sudo apt install lprng
sudp apt-get install hplip
sudo apt-get install hplip-ppds
hp-setup -gi 192.168.4.50 # local ip of network printer

list printers: lpstat -p
print document: lp -d HPLJ -o media=a4 -o sides=one-sided ~/files/test_file



#--------------- pubsub ---------------------------------

python3 pubsub.py --endpoint am6j7nlhi3tht-ats.iot.us-west-2.amazonaws.com --ca_file /home/pi/.ssh/AmazonRootCA1.pem --cert /home/pi/.ssh/certificate.pem --key /home/pi/.ssh/certificate.private.key