#!/usr/bin/env python

import datetime
import sys
import time
import pika
import os

parameters = pika.URLParameters(os.environ['AMQP_DSN'])
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.queue_declare(queue='hello')

content = ''
for line in sys.stdin:
	content = content + line
channel.basic_publish(exchange='',
                      routing_key='hello',
                      body=content)

connection.close()