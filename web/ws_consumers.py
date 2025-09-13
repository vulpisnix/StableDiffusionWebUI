from channels.generic.websocket import JsonWebsocketConsumer

from web import sd_queue_thread
from web.models import SDImageQueue

WS_Create = []
class WSConsumer_Create(JsonWebsocketConsumer):
    def connect(self):
        self.accept()
        WS_Create.append(self)

    def disconnect(self, code):
        WS_Create.remove(self)

    def receive_json(self, content, **kwargs):
        event = content['event']
        data = content['data']

        user = self.scope["user"]
        if not user.is_authenticated: return

        if event == 'create':
            qData = SDImageQueue.objects.create(
                user=user,
                action_type=data['event_type'],
                settings=data
            )
            qData.save()
            sd_queue_thread.queue.put(qData)
            sd_queue_thread.run()