import os
import pika
from parser import EmailParser
from persister import EmailPersister

parameters = pika.URLParameters(os.environ['AMQP_DSN'])
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue='hello')

parser = EmailParser()
persister = EmailPersister()

def callback(ch, method, properties, body):
  content = body.decode('utf-8')
  sender, tos, ccs, messageId, inReplyTo, subject, body = parser.parseEmail(content)
  persister.persistEmail(sender, tos, ccs, messageId, inReplyTo, subject, body)


channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()

