from blinker import signal

# class Processor:
#     def __init__(self, name):
#         self.name = name
#
#     def go(self):
#         ready = signal('ready')
#         ready.send(self)
#         print("Processing.")
#         complete = signal('complete')
#         complete.send(self)
#
#
#     def __repr__(self):
#         return '<Processor %s>' % self.name
#
#
# def subscriber(sender):
#     print("Got a signal sent by %r" % sender)
#
# def b_subscriber(sender):
#     print("Caught signal from processor_b.")
#     assert sender.name == 'b'


send_data = signal('send-data')


@send_data.connect
def receive_data(sender, **kw):
    print("Caught signal from %r, data %r" % (sender, kw))
    return 'received!'


result = send_data.send('anonymous', abc=123)

# ready = signal('ready')
# ready.connect(subscriber)
#
#
# processor_a = Processor('a')
# processor_a.go()
#
#
#
# processor_b = Processor('b')


# ready.connect(b_subscriber, sender=processor_b)
#
#
# processor_b.go()
#
