# -*- coding: utf-8 -*-
import os
import json
import pymongo

host = 'mongodb://pdurivage:zsVjnTWepfrwDyrsWxqqGjD2@ds151068.mlab.com:51068/textmeplz'
mongo = pymongo.MongoClient(host)

db = mongo.textmeplz
path = '/Users/paul4611/Downloads/27adxBLS8x09JrXIRm0ngF/accounts/'

for fname in os.listdir(path):
    f = os.path.join(path, fname)
    fp = open(f)
    data = json.load(fp)
    update = {
      "email": data['email'],
      "first_name": data['givenName'],
      "last_name": data['surname'],
      "password": data['password'],
    }
    result = db.user.find_one_and_update({'email': data['email']}, {'$set': update}, {'upsert': True})
    if result:
        print "Migrated", data['email']
