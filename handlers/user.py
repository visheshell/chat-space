import tornado.websocket
import tornado.escape
import logging
import uuid

from .base import BaseHandler
from commands import commands


class UserHandler(BaseHandler, tornado.websocket.WebSocketHandler):
    rooms = set()
    cache = []
    cache_size = 200
    default_send_room = None

    def open(self):
        self.default_send_room = self.application.initial_room
        for subscriber in self.default_send_room.subscribers:
            try:
                message = {
                    'html': '<div class="message" style="text-align: center"><b>%s</b> joined room <b>%s</b></div>' % (
                        self.get_current_user().decode('utf-8'), self.default_send_room.name)}
                subscriber.write_message(message)
            except:
                logging.error("Error sending message", exc_info=True)
        self.application.initial_room.subscribers.add(self)
        self.rooms.add(self.application.initial_room)
        self.write_message({'html': '<div class="message" style="text-align: center">Hello there! Type <b>/help</b></div>'})

    def on_close(self):
        if self.rooms:
            for room in self.rooms:
                room.remove_user(self)

    def connect_room(self, new_room):
        self.rooms.add(new_room)

    def send_updates(self, message):
        for subscriber in self.default_send_room.subscribers:
            try:
                message_template = 'self_message.html' if self == subscriber else 'message.html'
                message['html'] = tornado.escape.to_basestring(
                    self.render_string(message_template, message=message))
                subscriber.write_message(message)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        parsed = tornado.escape.json_decode(message)
        body_text = parsed["body"]

        for command in commands:
            temp = command['regex'].fullmatch(body_text)
            if temp:
                self.write_message({'html': '<div class="message" style="text-align: right">%s</div>' % body_text})
                if temp.groupdict():
                    command['handler'](self, temp.groupdict()['param'])
                else:
                    command['handler'](self)
                return

        data = {
            "id": str(uuid.uuid4()),
            "body": body_text,
            "user": self.get_current_user().decode('utf-8'),
            "room": self.default_send_room.name
        }
        self.send_updates(data)
