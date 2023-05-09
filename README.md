# AWS Native Connected Printer


## About this Project

This solution deploys backend Amazon Web Services (AWS) resources to support a fully cloud-based and event-driven Connected Printer solution using AWS IoT Core and the [AWS Cloud Development Kit (AWS CDK) developed in Python](https://docs.aws.amazon.com/cdk/latest/guide/work-with-cdk-python.html). This solution will also deploy a front-end react application for interacting with the backend resources.

Deploying this solution does not guarantee an organization’s compliance with any laws, certifications, policies, or other regulations.

## What You'll Build

![AWS Native Connected Printer](https://github.com/aws-samples/aws-iot-connected-printer/blob/main/AWS%20Native%20Connected%20Printer.png)

## How to Deploy

### Prerequisites

1. [Install Python 3.8](https://www.python.org/downloads/release/python-380/)
2. [Install Node and NPM](https://nodejs.org/en/download/)
3. [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
4. [Install the AWS CDK Tool](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)

### Back End Resources
First, you'll deploy the backend resources using CDK. Detailed instructions can be found at [./connected_printer_cdk/README.md](https://github.com/aws-samples/aws-iot-connected-printer/blob/main/connected_printer_cdk/README.md)

### Provision Your Device
Then, you'll need to provision your IoT Device. Check out the instructions at [./connected_printer_device/README.md](https://github.com/aws-samples/aws-iot-connected-printer/blob/main/connected_printer_device/README.md)

### Lastly, Interact with these Resources using a Web App
Follow the instructions found at [./connected_printer_frontend/README.md](https://github.com/aws-samples/aws-iot-connected-printer/blob/main/connected_printer_frontend/README.md)

## Costs and Licenses

You are responsible for the cost of the AWS services used while running this solution. There is no additional cost for using the solution.

This solution includes configuration parameters that you can customize. Some of these settings, such as instance type, affect the cost of deployment. For cost estimates, refer to the pricing pages for each AWS service you use. Prices are subject to change.

There are no licensing costs for this solution.