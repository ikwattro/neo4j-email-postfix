from email.message import EmailMessage
from email.parser import BytesParser, Parser
from email.policy import default
import email
import re
import talon
from talon import quotations
from talon.signature.bruteforce import extract_signature
pattern = "([\w ]+)(?:[ <>]+)([\w\.-]+@[\w\.-]+)"
talon.init()

class EmailParser:

  def parseEmail(self, s):
    headers = Parser(policy=default).parsestr(s)
    sender = self.extractSender(headers['from'])
    tos = self.extractRecipients(headers['to'])
    ccs = self.extractRecipients(headers['cc'])
    subject = headers['subject']
    messageId = headers['Message-Id']
    inReplyTo = headers['In-Reply-To']
    body = self.extractBody(s)

    # if self.isForwardedMessage(s) or body.endswith('Begin forwarded message:'):
    #   print("email is redirection")
    #   oldFrom = self.extractAddressLineFromForwardedText(newbody, 'From')
    #   if oldFrom is not None:

    return (sender, tos, ccs, messageId, inReplyTo, subject, body)

  
  def extractSender(self, addr):
    return self.emailMetadataFromString(addr)
  
  def extractRecipients(self, addrs):
    tos = []
    if addrs is None:
      return tos
    for addr in addrs.split(','):
      tos.append(self.emailMetadataFromString(addr.strip()))
    
    return tos
  
  def emailMetadataFromString(self, s):
    match = re.search(pattern, s)
    name = None
    address = None
    if match is not None and len(match.groups()) > 1:
      name = match.group(1)
      address = match.group(2)
    else:
      address = s
    
    return {'name': name, 'address': address}
  
  def extractBody(self, s):
    body = self.extractBodyFromEmail(s)
    reply = quotations.extract_from_plain(body)
    text, signature = extract_signature(reply)

    return text
  
  def extractBodyFromEmail(self, s):
    b = email.message_from_string(s)
    isMulti = b.is_multipart()

    if isMulti:
      for part in b.walk():
        ctype = part.get_content_type()
        cdispo = str(part.get('Content-Disposition'))
        if ctype == 'text/plain' and 'attachment' not in cdispo:
          body = part.get_payload(decode=True)
        # if ctype == 'application/pdf':
        #   pl = part.get_payload(decode=True)
        #   pl = base64.b64decode(pl)
        #   filename = part.get_filename()
        #   print('Attchment: {}'.format(filename))
        #   file = open(filename, 'wb')
        #   file.write(pl)
        #   file.close()
    else:
      body = b.get_payload(decode=True)
    
    return body.decode('utf-8')
  
  def isForwardedMessage(self, s):
    body = self.extractBodyFromEmail(s)
    if body.strip().lower().startswith('begin forw'):
      return True
    return False
  
  def extractAddressLineFromForwardedText(self, s, m):
    print("detecting new from address from forwarded message")
    body = s.strip().split('\n')
    for line in body:
      if line.startswith(m + ':'):
        print(line)


    