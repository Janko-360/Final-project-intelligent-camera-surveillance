
# Helper functions for the server side sse implementation

# This is a part of the SSE for the Flask server. 
# This one is customized to not need Redis
# Code form https://maxhalford.github.io/blog/flask-sse-no-deps/


import queue

class MessageAnnouncer:
    def __init__(self):
        self.listeners = {}

    def listen(self, client_addr):
        if client_addr not in self.listeners.keys():
            self.listeners[client_addr] = []  
        q = queue.Queue(maxsize=5)
        self.listeners[client_addr].append(q)
        return q

    def announce(self, msg, client_addr):
        # print("Announcing to listeners: ")
        # print(self.listeners)
        if client_addr in self.listeners.keys():
            messages = self.listeners[client_addr]
            # print(self.listeners)
            # print(messages)
            for i in reversed(range(len(messages))):
                try:
                    messages[i].put_nowait(msg)
                except queue.Full:
                    print('>>> Announcer had to delete a message')
                    del messages[i]

def format_sse(data: str, event=None) -> str:
    """Formats a string and an event name in order to follow the event stream convention.

    >>> format_sse(data=json.dumps({'abc': 123}), event='Jackson 5')
    'event: Jackson 5\\ndata: {"abc": 123}\\n\\n'

    """
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg
