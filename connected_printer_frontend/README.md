# AWS Native Connected Printer - Front End


## Prerequisites

1. CD into `connected_printer_frontend` and run ```npm install``` to install all dependencies the React Application Requires.
2. You'll need to register with the user pool we created in the cdk deployment package. To do this, replace the client-id value with the output from your cdk deploy for connected-printer-cdk.cognitoappclientid.
3. You'll also need to change the username to an email you have access to, and the password to something unique.
```
aws cognito-idp admin-create-user \
    --user-pool-id <Get this from cdk outputs> \
    --username <An email address you have access to> \
    --password <Choose a complicated password (mix of upper, lower, alphanumeric and at least one symbol, min 8 characters)> \
    --user-attributes Name="email",Value="<An email address you have access to>" Name="family_name",Value="Foobar" \
    --region us-west-2 
```
4. Next, you'll want to confirm your newly registered user in the Cognito Userpool. To do this, you'll also use the CLI (replace the user-pool-id with the output for connected-printer-cdk.cognitoappclientid):
```
aws cognito-idp admin-confirm-sign-up \
    --user-pool-id <Get this from cdk outputs> \
    --username <An email address you have access to> \
    --region us-west-2
```
5. Now that you've registered, we need to connect our front end application to the user pool so you can successfully log in. To do this, navigate to `src/index.js`, and change the userPoolId so that it matches the output for `connected-printer-cdk.cognitouserpoolclientid`, and the UserPoolWebClientId so that it matches the output for `connected-printer-cdk.cognitoappclientid`.
6. Next, run ```npm start``` to start the development server. Your browser should automatically open to `localhost:3000`, but you'll want to go to `localhost:3000/print` to view the actual app.


