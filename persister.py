from neo4j.v1 import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost')
session = driver.session()

class EmailPersister:

  def persistEmail(self, sender, tos, ccs, messageId, inReplyTo, subject, body):
    self.persistAddresses([sender])
    self.persistAddresses(tos)
    self.persistAddresses(ccs)
    self.persistContent(messageId, subject, body)
    self.relateAddressToEmail([sender], messageId, 'FROM')
    self.relateAddressToEmail(tos, messageId, 'TO')
    self.relateAddressToEmail(ccs, messageId, 'CC')
    self.relateReplyTo(messageId, inReplyTo)
    self.processNLP(messageId)
  
  def persistAddresses(self, addresses):
    q = "UNWIND $addresses AS address MERGE (n:EmailAddress {id: address.address}) SET n.name = address.name"
    session.run(q, addresses=addresses).consume()
  
  def persistContent(self, messageId, subject, body):
    q = """
    MERGE (e:Email {messageId: $id}) SET e.body = $body, e.subject = $subject
    """
    session.run(q, id=messageId, body=body, subject=subject).consume()
  
  def relateAddressToEmail(self, addresses, messageId, rel):
    q = """
    MATCH (e:Email {messageId: $id})
    UNWIND {addrs} AS address
    MATCH (a:EmailAddress {id: address.address})
    MERGE (e)-[:%s]->(a)
    """
    query = q % (rel)
    session.run(query, id=messageId, addrs=addresses).consume()
  
  def relateReplyTo(self, messageId, originalId):
    if originalId is None:
      return
    q = """
    MATCH (c:Email {messageId: $messageId})
    MATCH (o:Email {messageId: $originalId})
    MERGE (c)-[:REPLY_TO]->(o)
    """
    session.run(q, messageId=messageId, originalId=originalId).consume()
  

  def processNLP(self, messageId):
    # Annotate
    q = """
    MATCH (n:Email) WHERE n.messageId = $id AND NOT (n)-[:HAS_ANNOTATED_TEXT]->()
    CALL ga.nlp.annotate({id: id(n), text: n.subject + '.' + n.body, pipeline:'email', checkLanguage: false}) 
    YIELD result 
    MERGE (n)-[:HAS_ANNOTATED_TEXT]->(result)
    """
    session.run(q, id=messageId).consume()

    # extract keywords 
    q = """
    MATCH (n:Email)-[:HAS_ANNOTATED_TEXT]->(at) WHERE n.messageId = $id AND NOT (at)<-[:DESCRIBES]-()
    CALL ga.nlp.ml.textRank({annotatedText: at, useDependencies: true})
    YIELD result
    WITH at
    CALL ga.nlp.ml.textRank.postprocess({annotatedText: at, method:'subgroups'})
    YIELD result
    RETURN count(*)
    """
    session.run(q, id=messageId).consume()