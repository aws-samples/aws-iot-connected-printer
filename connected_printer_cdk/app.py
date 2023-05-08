#!/usr/bin/env python3

import aws_cdk as cdk


from connected_printer_cdk.connected_printer_cdk_stack import ConnectedPrinterCdkStack


app = cdk.App()
ConnectedPrinterCdkStack(app, "connected-printer-cdk")

app.synth()
