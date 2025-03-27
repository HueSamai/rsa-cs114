import socket
from packet import Packet
from select import select

class Client:
    singleton = None
    _message_handlers = {}

    ip = '127.0.0.1'
    port = 8080

    socket = None

    def __init__(self):
        Client.singleton = self
        Client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Client.socket.connect((Client.ip, Client.port))
        Client.inputs = [self.socket]
    
    @staticmethod
    def register_message_handler(id, func):
        if Client.singleton is None:
            Client.singleton = Client()
        Client._message_handlers[id] = func
    
    @staticmethod
    def handle_message(packet: Packet):
        if packet.msg_id not in Client._message_handlers:
            print(f"Invalid packet received with id {packet.msg_id}")
            return

        Client._message_handlers[packet.msg_id](packet)

    @staticmethod
    def loop():
        if Client.singleton is None:
            raise Exception("Attempted to start client loop, when no client has been initialised")

        while True:
            readable, _, _ = select(Client.inputs, [], Client.inputs, 0.5)

            for sock in readable:
                Client.resolve_packets(sock) 

    @staticmethod
    def resolve_packets(sock) -> bool:
        try:
            length = sock.recv(4)
        except ConnectionResetError:
            return True

        length = int.from_bytes(length, 'little')
        if length == 0:
            return True

        data = sock.recv(length)

        packet = Packet(int.from_bytes(data[:4], 'little'))
        packet.write(data[4:])
        
        Client.handle_message(packet)

        return False

    @staticmethod
    # if addresses is None then it is sent to all
    def send_packet(packet): 
        if Client.socket is None:
            return
        Client.socket.send(packet.format_to_send())

class MessageHandler:
    @staticmethod
    def register(message_id):
        def decorator(function):
            Client.register_message_handler(message_id, function)
            return function
        return decorator    


