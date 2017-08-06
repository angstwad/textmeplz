# coding: utf-8

from mongo import get_mongoconn
from textmeplz.utils import create_mailgun_route, delete_mailgun_route

mongoconn = get_mongoconn()

no_route = []
has_route = []
for doc in mongoconn.User.find():
    if not doc['mailgun_route_id']:
        no_route.append(doc)
    else:
        has_route.append(doc)

for doc in no_route:
    print "Processing %s." % doc['mailhook_id']
    resp = create_mailgun_route(**doc)
    doc['mailgun_route_id'] = resp['route']['id']
    delete_mailgun_route(**doc)
    doc['enabled'] = False
    doc.save()

for doc in has_route:
    print "Marking %s as enabled." % doc['mailhook_id']
    doc['enabled'] = True
    doc.save()
