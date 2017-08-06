from datetime import datetime, timedelta
from textmeplz.utils import get_twilio
from gevent.queue import JoinableQueue
import gevent
from gevent import monkey
monkey.patch_all()

seven_days_ago = datetime.now() - timedelta(days=7)
tasks = JoinableQueue()
tw = get_twilio()
msgsiterable = tw.messages.iter(after=seven_days_ago)

print "Getting all messages from Twilio."
count = 0
for msg in msgsiterable:
    tasks.put(msg)
    count += 1
    if count % 50 == 0:
        print "Got %s messages." % count


def process_messages(thread_num):
    print "Thread %s starting up." % thread_num
    while not tasks.empty():
        msg = tasks.load()
        try:
            for media in msg.media_list.list():
                print "Thread %s deleting media %s" % (thread_num, media.sid)
                media.delete()
        except:
            pass
    print "Thread %s done." % thread_num


threads = [gevent.spawn(process_messages, num) for num in range(25)]
gevent.joinall(threads)
