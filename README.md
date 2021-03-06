# Using Serverless computing and Lambda for Network Automation

I've recently been studying for the AWS Associate Architect certification when I came across the concept of Serverless functions, which are known as Lambda functions in AWS but are also available in other cloud platforms under different guises. Serverless gives you and environment in which you can upload you code (from pretty much any language of your choosing) once the code is setup as a Lambda function you can then trigger it to run with events. Events could be something as simple as a file being uploaded into a datastore or an HTTP/REST call to an API gateway which is set up to redirect to the Lambda. When it comes to automation, having an environment like this that allows us to build, store and trigger our code from can be quite a useful tool. No longer do we have to set up a Raspberry Pi or run around trying to find a server to install Linux on, we simply write our function and set a trigger which will run the code.

In this guide we'll explore some potential usecases of this technology and walkthrough a practical example. When it comes to network automation we often need a compute environment in which to host our scripts and workflows, serverless negates the need for that to be a dedicated compute enivornment aslong as our code is built in the right way. The obvious benefit to this is cost, instead of needing to pay for and maintain a dedicated server billing is carried out per 'event' which leads to considerable opex savings.

My initial thoughts for this was as I have been using a lot of tools such as Terraform and Anisble recently was to put the workflows built with these tools behind Lambda functions and call on them in a consistent way such as an API gateway. Therefore rather than focus on the tools, automation teams can automate the tasks they need to but provide a consistent way to themselves and other teams to automate their services and provide a service. Imagine a scenario such as below, where an automation team that uses multiple tools such as Ansible, Terraform, and their own custom scripts can host these as indivdual Lambda functions and expose them as a simple API.

![](./images/API-Gateway.png)

However after much experimentation this ended up not being feasible as to package up the function with the required dependancies made the packages too large for Lambda to be able to support. So as this wasn't possible I decided to start off with a simpler example, build a workflow in Python using the API's of the individual platform to build a basic task. 

As an example I've used the workflow of creating a branch in Meraki. However this could be pretty much anything you want to automate, if you can write it in a language such as Python, Go or anything else that Lambda supports and aslong as you have access to the API or device you want to automate from your AWS region you should be able to run it from Lambda. 

![](./images/workflow.png)

Having such a concept of would allow you to build a series of workflows, potentially using different tools, platforms or languages but have a consistent way of invoking these workflows through calling an API gateway for example.

## Create your workflow in code

In this example we'll be focusing on Python as it's today by far the most popular language for network automation, however you have many options for runtimes to build your functions on including Go, NodeJS, Java, Ruby and .NET.

So first off you'll need your code, when building you're code especially if you're passing data to your function in there's a few characterisics of building for Lambda that we need to adapt to but I'll try cover most of it in this guide so that you can adapt this to you're own environment and usecase. 

First you can see here our code is split into functions:

##### main(events, context)

The variable events which is passed into this function will include the parameters from the HTTP body that is passed from our API gateway, the main function parses this and then calls each of the functions below in order to complete our desired workflow.

The main() function is called by our Lambda function at runtime when an event triggers our code. Upon sucessful run this will return a HTTP code 200 with the message "Success, network has been created!"

You will notice on this function we pass in two parameters, events and context.

Events will pass user defined information to our function, for example it will pass in the parameters from our API call in the HTTP body from our API gateway. You can see this in the code from the dictionary element 'event['body']' which is passed into our function.

Context provides information about how your Lambda has been triggered and other useful information, we'll leave Context to one side as we won't use it in this guide.

##### create_Network(event)

This is the first function which is called from main. Calls the API in Meraki which creates a new network in the Meraki dashboard

Also returns the variable networkID which is required by later functions.

##### claimDevices(event, networkID)

Calls the API in Meraki to claim our devices to our newly created network, will look round the devices dictionary from our HTTP body and add all the devices that are present with valid serial numbers.

##### updateDevices(event)

Updates the newly claimed devices with specific information including device location and name. 

Device name is a concatenation on network name and device type which is carried out by this function.

##### bindTemplate(event, networkID)

Binds a template to our newly created network to automate device configuration.

The code in it's entirety can be seen below:

```python
import requests
import json

def main(event, context):

    event = json.loads(event['body'])

    networkID = create_network(event)

    claimDevices(event, networkID)

    updateDevices(event)

    bindTemplate(event, networkID)

    return {
        'statusCode': 200,
        'body': json.dumps('Success, network has been created!')
    }

def create_network(event):

    url = "https://api-mp.meraki.com/api/v1/organizations/" + event['orgID'] +"/networks"

    payload = "{\n    \"name\": \""+ event['networkName'] +"\",\n    \"productTypes\": [\n        \"appliance\",\n        \"switch\",\n        \"wireless\"\n    ],\n    \"timeZone\": \"" +event['timezone']+ "\"\n}"
    headers = {
      'Content-Type': 'application/json',
      'X-Cisco-Meraki-API-Key': event['auth']
    }


    response = requests.request("POST", url, headers=headers, data = payload)


    parsed_json = (json.loads(response.text.encode('utf8')))

    networkID = parsed_json['id']

    return networkID

def claimDevices(event, networkID):


    url = "https://api-mp.meraki.com/api/v1/networks/"+ networkID +"/devices/claim"
    
    print(event['devices'])

    for item in event['devices']:
        item = event['devices'][item]['serial']

        payload = "{\n    \"serials\": [\n        \"" + item + "\"\n    ]\n}"
        headers = {
          'Content-Type': 'application/json',
          'X-Cisco-Meraki-API-Key': event['auth']
        }

        response = requests.request("POST", url, headers=headers, data = payload)

def updateDevices(event):


    for item in event['devices']:
        
        serial = event['devices'][item]['serial']
        type = event['devices'][item]['type']
        address = event['devices'][item]['address']

        deviceName = event['networkName'] + "_" + type
        print(deviceName)

        url = "https://api-mp.meraki.com/api/v1/devices/" + serial

        payload = "{\n    \"name\": \"" + deviceName + "\",\n    \"address\": \"" + address +"\",\n    \"moveMapMarker\": \"True\"\n}"
        print(payload)
        headers = {
        'Content-Type': 'application/json',
        'X-Cisco-Meraki-API-Key': event['auth']
        }

        response = requests.request("PUT", url, headers=headers, data = payload)

def bindTemplate (event,networkID):

    url = "https://api-mp.meraki.com/api/v1/networks/"+ networkID +"/bind"

    payload = "{\n    \"configTemplateId\": \""+ event['templateID'] +"\",\n    \"autoBind\": \"False\"\n}"
    headers = {
      'Content-Type': 'application/json',
      'X-Cisco-Meraki-API-Key': event['auth']
    }

    response = requests.request("POST", url, headers=headers, data = payload)
```

## Packaging up our code and creating a Lambda function

One of the first idiosyncracies of using Lambda is how we package up and upload our code to the service, especially if you have library dependancies in Python which you need to package up with your code, in this example we have to do this for the requests module which isn't included in the Lambda python interpreter and has to be uploaded as a package.

To begin, on your local machine navigate to the same directory as your main.py file, if you have cloned this repo that is under the directory 'code'. To get our libraries in a new, project-local package directory use the pip command with the --target option.

```bash
pip install --target ./package requests
cd package
```

Now thats done, create a ZIP archive of the dependencies.

```bash 
zip -r9 ${OLDPWD}/function.zip .
```

And add your function code to the archive also

```
cd $OLDPWD
zip -g function.zip main.py
```

![](./images/create-zip.gif)

Now you have your function.zip archive, it's time to upload this to your Lambda function. But first lets create a Lambda function. To do this search for the "Lambda" service from your management console on AWS and go to the function section, from there you should see the "Create function" option, select this and use the create from scratch wizard to create your function (ensure the runtime is set to Python 3.8).

![](./images/lambda-create.gif)

Now that the function has been created, upload your newly created function.zip archive which hosts your code and packages, you can find this from the actions button under the "Function code" section,

![](./images/zip-upload.gif)

Now our code is uploaded to the function we have to edit some of the settings for when the code is run, scroll down the page to "Basic settings" and press edit. First set the timeout to be around a minute, it should take around 20-30 seconds for our function to run, therefore the 3 second timeout has to be increaed or our function will never work. Also change the handler to "main.main" this means when the function runs it will look in the main.py file and run the main function. Remember this when you design your code as you can only invoke a single function in a lambda event.

![](./images/change-handler.gif)

## Building an API gateway

Now we have our function ready we need a way to invoke the function from an event. In this example we're going to do this through invoking an API that we're going to create from AWS's API gateway service

As you get more advanced, you can add extra layers of authentication and additional features to the API. But for this example we're going to keep it simple.

First we need to create our API gateway, to do this search for the "API Gateway" service from your management console on AWS and go to the function section, from there you should see the "Create API" option, select this and use the create from scratch wizard to create your function (ensure the runtime is set to Python 3.8).

![](./images/create-gateway.gif)

Once you've created your gateway, it's time to add some resources and methods. From the resources section, select actions and click on create resource. This will be the REST endpoint that you're API will serve. Once you've gave it a name then select create method and select "POST"

![](./images/create-method.gif)

## Invoking our API

Now all thats left to do is to test out our API and invoke our function. To do this select the method "POST" of the resource we created earlier. It should take you to the "POST - Method Execution" screen which shows a workflow of what will happen when the API runs.

```json
{
  "auth": "your-auth-key-here",
  "orgID": "123456",
  "timezone": "Europe/London",
  "networkName": "testNetwork",
  "templateID": "L_123456789",
  "devices": {
    "Device-1": {
      "serial": "XXXX-XXXX-XXXX",
      "address": "310 St Vincent St, Glasgow G2 5RG",
      "type": "MX68"
    },
    "Device-2": {
      "serial": "XXX-XXX-XXXX",
      "address": "310 St Vincent St, Glasgow G2 5RG",
      "type": "MR33"
    }
  }
}
```

As you can see above theres an example JSON body that our function is expecting, edit this with your own credentials and details and paste this into the "Request Body" section of the form (ensuring a properly formatted JSON body is crucial for this to work correctly. When you reach the bottom of the form press the "Test" button and wait. The function may take up to 30 seconds to complete, as it runs you can refresh the Meraki dashboard to see the actions being carried out as the function runs, you should see the network being created and devices being updated as it goes. Once it's complete the response will show ""Success, network has been created!"" as the animated diagram shows below.

![](./images/invoke-api.gif)

Now all that's left to do is deploy your API. Using the "deploy API" option from the actions drop down. Create a new stage, call it whatever you want here. 

![](./images/deploy-api.gif)

Finally, now the API has been published, it can be accessed using tools such as Postman as can be seen from the graphic below.

![](./images/postman.gif)

Congratulations, you've just set up your first Lambda function and built your first API gateway! Great work!
