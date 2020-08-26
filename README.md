# Using Serverless computing and Lambda for Network Automation

I've recently been studying for the AWS Associate Architect certification when I came across the concept of Serverless functions, which are known as Lambda functions in AWS. Serverless gives you and environment in which you can upload you code (from pretty much any language of your choosing) once the code is setup as a Lambda function you can then trigger it to run with events. Events could be something as simple as a file being uploaded into a datastore or an API call to an API gateway which is set up to redirect to the Lambda. When it comes to automation, having an environment like this that allows us to build, store and trigger our code from can be quite a useful tool. In this guide we'll explore some potential usecases of this technology and walkthrough a practical example.

My initial thoughts for this was as I have been using a lot of tools such as Terraform and Anisble recently could I put the workflows I build these tools behind Lambda functions and call on them in a consistent way such as an API gateway. Therefore rather than focus on the tools, automation teams can automate the tasks they need to but provide a consistent way to themselves and other teams to automate their services. Imagine a scenario such as below, where an automation team that uses multiple tools such as Ansible, Terraform, and their own custom scripts can host these as indivdual Lambda functions and expose them as a simple API.

However after much experimentation this ended up not being feasible as to package up the function with the required dependancies made the packages too large for Lambda to be able to support. So as this wasn't possible I decided to start off with a simpler example, build a workflow in Python using the API's of the individual platform to build a basic task.

As an example I've used the workflow of creating a branch in Meraki. However this could be pretty much anything you want to automate, if you can write it in a language such as Python, Go or anything else that Lambda supports and aslong as you have access to the API or device you want to automate from your AWS region you should be able to run it from Lambda. 

Create network API --> Claim devices to network --> Update devices with names/location --> Bind a template to the network

## Create your workflow in code

Having such a concept of would allow you to build a series of workflows, potentially using different tools, platforms or languages but have a consistent way of invoking these workflows through calling an API gateway for example.

In this example we'll be focusing on Python as it's today the most popular language for network automation

So first off you'll need your code, when building you're code especially if you're passing data to your function in there's a few characterisics of building for Lambda that we need to adapt to but I'll try cover most of it in this guide so that you can adapt this to you're own environment and usecase. 

First you can see here our code is split into functions

##### main(events, context)

The variable events which is passed into this function will include the parameters from the HTTP body that is passed from our API gateway, the main function parses this and then calls each of the functions below in order to complete our desired workflow

The main() function is called by our Lambda function at runtime when an event triggers our code.

##### create_Network(event)

Calls the API in Meraki which creates a new network.

Also returns the variable networkID which is required by later functions

##### claimDevices(event, networkID)

Calls the API in Meraki to claim our devices to our newly created network, will look round the devices dictionary from our HTTP body

##### updateDevices(event)

Updates the newly claimed devices with specific information including device location and name. 

Device name is a concatenation on network name and device type.

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
        'body': json.dumps('Sucess, network has been created!')
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

## Packaging up our code

One of the first idiosyncracies of using Lambda is how we package up our code, especially if you have library dependancies in Python

Hopefully you should have

```bash
pip install --target ./package requests
cd package
```

```bash 
zip -r9 ${OLDPWD}/function.zip .
```

```
cd $OLDPWD
zip -g function.zip lambda_function.py
```

Now you have your function.zip archive, it's time to upload this to your Lambda function

## Building an API gateway

Now we have our code 

## Invoking our API

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
