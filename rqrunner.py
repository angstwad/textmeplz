import sys
from redis import Redis
from rq import Queue, Connection, Worker

from textmeplz.config import config

# Preload libraries
import twilio

# Provide queue names to listen to as arguments to this script,
# similar to rqworker

redis_conn = Redis(config.REDIS_HOST)

with Connection(redis_conn):
    qs = map(Queue, sys.argv[1:]) or [Queue()]
    w = Worker(qs)
    w.work()
