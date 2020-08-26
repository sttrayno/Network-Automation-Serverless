# Using Serverless computing and Lambda for Network Automation

I've recently been studying for the AWS Associate Architect certification when I came across the concept of Serverless functions, which are known as Lambda functions in AWS. Serverless gives you and envrionment in which you can upload you code (from pretty much any language of your choosing) once the code is setup as a Lambda function you can then trigger it to run with events. Events could be something as simple as a file being uploaded into a datastore or an API call to an API gateway which is set up to redirect to the Lambda. When it comes to automation, having an environment like this that allows us to build, store and trigger our code from can be quite a useful tool.

My initial thoughtsfor this was as I have been using a lot of tools such as Terraform and Anisble recently could I stick these behind a Lambda function and call on them in a consistent way such as an API gateway, however after much experimentation this ended up not being feasible as to package up the function with the required dependancies made the packages too large for Lambda to be able to support. So as this wasn't I decided to start off with a more simpilier example, build a workflow in Python. As an example I've used the workflow of creating a branch in Meraki.

#### Create branch workflow

Create network API --> Claim devices to network --> Update devices with names/location --> Bind a template to the network

Having such a concept of this would allow you to build a series of workflows, potentially using different tools or languages but have a consistent way of invoking these workflows through calling an API gateway for example.

So first off you'll need your code, when building you're code especially if you're passing parameters in there's a few characterisics of building for Lambda that we need to adapt to but I'll try cover most of it in this guide so that you can adapt this to you're own environment and usecase.

```python
import requests
import json

def main(event, context):

    print(json.dumps(event))
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

## Building an API gateway

## Invoking our API

