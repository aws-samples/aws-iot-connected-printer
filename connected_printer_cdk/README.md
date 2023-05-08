# AWS Native Connected Printer - CDK


Get Started:
1. First, cd into the source directory for our CDK project with: ```cd connected_printer_cdk```

2. Next, we should create and active a python virtual envrionment. This allows us the ability to contain our python and python package version requirements without conflicting with other versions on our local system. 
```
python3 -m venv .venv 
source .venv/bin/activate
```

3. Next, install the python dependencies with: ```python3 -m pip install -r requirements.txt```

4. We can now bootstrap our environment with: ```cdk bootstrap aws://<account number>/<region> --profile <profile>``` (--profile flag is optional, remove if you want to use default aws cli credentials)

>If "No module named 'aws_cdk' error" on Step 6, or earlier:
>   Run `npm install -g aws-cdk@latest`

5. Before we can deploy this, we need to build a Lambda Layer for [PIL/pillow](https://pillow.readthedocs.io/). We will need to bundle the executables in a particular way, matching the path python3.8 will look for these executables in a Lambda Function. In addition, we'll need to use executables that work with the OS of our Lambda compute uses - to do this, we will install the package in a Cloud9 Environment that uses Amazon Linux 2.
    - If you are not running through this samples repository using Cloud9:
        - Create a Cloud9 Environment in the Console, and Launch the envrionment.
        - Install Amazon Linux Extras for python3.8, the runtime our Lambda Function uses with: `sudo amazon-linux-extras install python3.8`
        - Install pillow with `python3.8 -m pip install pillow --target=/home/ec2-user/environment/pillow/python3.8/site-packages`
        - Sync these executables with a directory in S3 so you can download them to your local working IDE with `aws s3 sync /home/ec2-user/environment/pillow/ s3://bucket/pillow`
        - Finally, sync the executables back to your local working directory with `aws s3 sync s3://bucket/pillow/ ~/.../connected_printer_poc/connected_printer_cdk/lambda_layer/layer/python/lib/`
    - If you are already using Cloud9 while deploying the connected_printer_poc samples repository, execute the following commands:
        - Install Amazon Linux Extras for python3.8, the runtime our Lambda Function uses with `sudo amazon-linux-extras install python3.8`
        - Install pillow with `python3.8 -m pip install pillow --target=/home/ec2-user/environment/connected_printer_poc/connected_printer_cdk/lambda_layer/layer/python/lib/python3.8/site-packages`
    - The executables that CDK will upload to AWS as a Lambda Layer are now available and you can continue with subsequent instructions.

6. We can now deploy the CDK project with: `cdk deploy --profile <profile>` (--profile flag is optional, remove if you want to use default aws cli credentials)

7. CDK will print Outputs following deployment of the resources therein. You'll need to update a few commands and variables found in:
    - `../connected_printer_device/README.md`
        - Under **Get a Claim on Your Provisioning Cert** and **Provision the Thing**, replace the --template-name flag value with the value from connected-printer-cdk.provisioningtemplatename
    - `../connected_printer_frontend/src/Print.JS`
        - Update (line 7) const front_end_api_base_uri = `value from connected-printer-cdk.connectedprinterapiEndpointxxxxxxxx`

8. With that, all the backend resources our workload uses are created in AWS. 

9. Next, we'll provision our IoT Device. Head on over to [connected_printer_device/README.md](https://github.com/aws-samples/aws-iot-connected-printer/blob/main/connected_printer_device/README.md) for further instructions.


