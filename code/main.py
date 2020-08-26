import requests
import json

AUTH = "6a572db444bffb6bbf5cd68011e745f217e36121"

timezone = "Europe/London"

orgID = "952492"

devices = {
  "device1" : {
    "serial" : "Q2BN-TXYH-KJLU",
    "address" : "28 Avondale Grove, East Kilbride, Glasgow G741BF",
    "type" : "MX64"
  },
  "device2" : {
    "serial" : "Q2BN-HN5M-CKFJ",
    "address" : "28 Avondale Grove, East Kilbride, Glasgow G741BF",
    "type" : "MX64"
     },
}
networkName = "testNetwork"

templateID = "L_706502191543762035"

def main(networkName):

    networkID = create_network(orgID, networkName, timezone)

    claimDevices(networkID, devices)

    updateDevices(devices, networkName)

    bindTemplate(networkID, templateID)


def create_network(orgID, networkName, timezone):

    url = "https://api-mp.meraki.com/api/v1/organizations/" + orgID +"/networks"

    payload = "{\n    \"name\": \""+ networkName +"\",\n    \"productTypes\": [\n        \"appliance\",\n        \"switch\",\n        \"wireless\"\n    ],\n    \"timeZone\": \"" +timezone+ "\"\n}"
    headers = {
      'Content-Type': 'application/json',
      'X-Cisco-Meraki-API-Key': AUTH
    }


    response = requests.request("POST", url, headers=headers, data = payload)


    parsed_json = (json.loads(response.text.encode('utf8')))

    networkID = parsed_json['id']

    return networkID


def claimDevices(networkID, serials):


    url = "https://api-mp.meraki.com/api/v1/networks/"+ networkID +"/devices/claim"

    for item in devices:

        item = devices[item]['serial']

        payload = "{\n    \"serials\": [\n        \"" + item + "\"\n    ]\n}"
        headers = {
          'Content-Type': 'application/json',
          'X-Cisco-Meraki-API-Key': AUTH
        }

        response = requests.request("POST", url, headers=headers, data = payload)


def updateDevices(devices, networkName):


    for item in devices:

        serial = devices[item]['serial']
        type = devices[item]['type']
        address = devices[item]['address']

        deviceName = networkName + "_" + type
        print(deviceName)

        url = "https://api-mp.meraki.com/api/v1/devices/" + serial


        payload = "{\n    \"name\": \"" + deviceName + "\",\n    \"address\": \"" + address +"\",\n    \"moveMapMarker\": \"True\"\n}"
        print(payload)
        headers = {
        'Content-Type': 'application/json',
        'X-Cisco-Meraki-API-Key': AUTH
        }

        response = requests.request("PUT", url, headers=headers, data = payload)



def bindTemplate (networkID, templateID):


    url = "https://api-mp.meraki.com/api/v1/networks/"+ networkID +"/bind"

    payload = "{\n    \"configTemplateId\": \""+ templateID +"\",\n    \"autoBind\": \"False\"\n}"
    headers = {
      'Content-Type': 'application/json',
      'X-Cisco-Meraki-API-Key': AUTH
    }

    response = requests.request("POST", url, headers=headers, data = payload)


main(networkName)
