import requests

# url = "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode=27011"

BUS_STOP_CODE = '27011'
BUS_SERVICE_NO = '199'

url = f'https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode={BUS_STOP_CODE}&ServiceNo={BUS_SERVICE_NO}'

payload = {}
headers = {
  'AccountKey': 'selurgv5RFiqXJ8Y27VvgA==',
  'accept': 'application/json'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)