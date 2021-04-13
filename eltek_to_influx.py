#!/usr/bin/python3
# Read data from Eltek Minipack via SNMP and send to InfluxDB
# (c) 2021 Piotr Smolen <komuch@gmail.com>

import json
from easysnmp import Session
from influxdb import InfluxDBClient

InfluxdHostname = 'grafana.local'
InfluxdPort = 8086
InfluxDatabase = 'eltek'

SNMPCommunity = 'public'
SNMPVersion = 2

influxclient = InfluxDBClient(host=InfluxdHostname, port=InfluxdPort)
influxclient.switch_database(InfluxDatabase)

# List of devices to read

eltek_list = [  ['eltek1', '192.168.1.1'],
]

# Parameters to read from SNMP

eltek_params = [['BatteryVoltageValue', '1.3.6.1.4.1.12148.10.10.5.5.0', 'voltage'],
                ['BatteryTemperaturesValue', '1.3.6.1.4.1.12148.10.10.7.5.0', 'other'],
                ['BatteryTimeLeftValue', '1.3.6.1.4.1.12148.10.10.8.5.0', 'other'],
                ['BatteryCurrentsValue', '1.3.6.1.4.1.12148.10.10.6.5.0', 'current'],
                ['BatteryTotalCapacityValue', '1.3.6.1.4.1.12148.10.10.11.5.0', 'other'],
                ['BatteryUsedCapacityValue', '1.3.6.1.4.1.12148.10.10.10.5.0', 'other'],
                ['BatteryRemainingCapacityValue', '1.3.6.1.4.1.12148.10.10.9.5.0', 'other'],
                ['BatteryQualityValue', '1.3.6.1.4.1.12148.10.10.9.5.0', 'other'],
                ['RectifierInputVoltageValue.1', '1.3.6.1.4.1.12148.10.5.6.1.4.1', 'voltage'],
                ['RectifierInputVoltageValue.2', '1.3.6.1.4.1.12148.10.5.6.1.4.2', 'voltage'],
                ['RectifierOutputCurrentValue.1', '1.3.6.1.4.1.12148.10.5.6.1.3.1', 'current'],
                ['RectifierOutputCurrentValue.2', '1.3.6.1.4.1.12148.10.5.6.1.3.2', 'current'],
                ['RectifiersCurrentValue', '1.3.6.1.4.1.12148.10.5.2.5.0', 'current'],
                ['LoadCurrentValue', '1.3.6.1.4.1.12148.10.9.2.5.0', 'current'],
                ['MainsVoltage', '1.3.6.1.4.1.12148.10.3.4.1.6.1', 'voltage'],
]

data = [{}]
data_temp = [{}]
resultarray = []

# Get data from device via SNMP
def getEltekSNMPData(ip):
        resultarray = []

        session = Session(hostname=ip, community=SNMPCommunity, version=SNMPVersion, timeout=30)

        for param in eltek_params:
                oid = param[1]
                result = session.get(oid)
                if result.value != 'NOSUCHINSTANCE':

                        resultarray += [[param[0], result.value]]
        return resultarray

# Main loop, create JSON from SNMP data
for eltek in eltek_list:
        loadpower = 1
        measure_result = getEltekSNMPData(eltek[1])
        for measurement in measure_result:
                #print(measurement[0])
                data_temp = { 'measurement': 'eltek', 'tags': {'eltek_name': eltek[0], 'measurement_type': measurement[0] }, 'fields': { 'value': int(measurement[1]) } }
                data.append(data_temp)
                
                # Calculate load power from battery voltage and load current
                if measurement[0] == 'BatteryVoltageValue' or measurement[0] == 'LoadCurrentValue':
                        loadpower *= int(measurement[1])

        data_temp = { 'measurement': 'eltek', 'tags': {'eltek_name': eltek[0], 'measurement_type': 'LoadPower' }, 'fields': { 'value': loadpower } }
        data.append(data_temp)

# Write JSON to InfluxDB as one query
try:
    influxclient.write_points(data)
except:
    print('Error!')

