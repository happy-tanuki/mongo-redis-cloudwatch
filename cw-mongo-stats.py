#!/usr/bin/env python3
'''
Send MongoDB usage metrics to Amazon CloudWatch

This is intended to run on an Amazon EC2 instance and requires a boto config 
(~/.boto) allowing to write CloudWatch metrics.
'''

from pymongo import MongoClient
from boto.ec2 import cloudwatch
from boto.utils import get_instance_metadata

def collect_mongo_info():
    host = 'localhost'
    port = 27017
    username = 'monitor'
    password = ''
    auth_source = 'admin'
    client = MongoClient(host=host, port=port, username=username, password=password, authSource=auth_source)
    return client.admin.command('serverStatus')

def send_multi_metrics(instance_id, region, metrics, unit='Count', namespace='EC2/MongoDB'):
    cw = cloudwatch.connect_to_region(region)
    cw.put_metric_data(namespace, list(metrics.keys()), list(metrics.values()),
        unit=unit, dimensions={"InstanceId": instance_id})

if __name__ == '__main__':
    metadata = get_instance_metadata()
    instance_id = metadata['instance-id']
    region = metadata['placement']['availability-zone'][0:-1]
    mongo_data = collect_mongo_info()

    count_metrics = {
        'CurrentConn': mongo_data['connections']['current'],
        'AvailableConn': mongo_data['connections']['available'],
        'CurrentQueue': mongo_data['globalLock']['currentQueue']['total'],
        'ActiveClients': mongo_data['globalLock']['activeClients']['total'],
        'ConcurrentWrite': mongo_data['wiredTiger']['concurrentTransactions']['write']['out'],
        'ConcurrentRead': mongo_data['wiredTiger']['concurrentTransactions']['read']['out']
    }

    byte_metrics = {
        'MongoMemory': mongo_data['mem']['resident'],
    }

    send_multi_metrics(instance_id, region, count_metrics)
    send_multi_metrics(instance_id, region, byte_metrics, 'Megabytes')
