#!/usr/bin/python3
# Read number of PPPoE connections from BRAS/LNG devices via SNMP and send to InfluxDB
# (c) 2021 Piotr Smolen

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

bras_list = [   ['10.2.2.7', 'redback'],
                ['10.2.2.9', 'mikrotik'],
                ['10.2.2.66', 'cisco'],
]

data = [{}]
data_temp = [{}]

# Get data from device via SNMP
def getSessions(ip, type):
        session = Session(hostname=ip, community=SNMPCommunity, version=SNMPVersion, timeout=30)

        if type == 'mikrotik':
                oid = '.1.3.6.1.4.1.9.9.150.1.1.1.0'
        elif type == 'redback':
                oid = '.1.3.6.1.4.1.2352.2.27.1.2.5.3.0'
        elif type == 'cisco':
                oid = '1.3.6.1.4.1.9.9.194.1.1.1'

        try:
                sessions = session.get(oid)
                return sessions.value
        except:
                return "0"

# Main loop, create JSON from SNMP data
for bras in bras_list:
        sessions = getSessions(bras[0], bras[1])
        data_temp = { 'measurement': 'pppoe_sessions', 'tags': {'bras_ip': bras[0], 'bras_type': bras[1] }, 'fields': { 'value': int(sessions) } }
        data.append(data_temp)


# Write JSON to InfluxDB as one query
try:
    influxclient.write_points(data)
except:
    print('Error!')

