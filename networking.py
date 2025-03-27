import socket
from select import select
import random
from typing import List
import packet_id
from packet import Packet

class Client:
    def __init__(self, id, socket):
        self.id = id
        self.socket = socket
        self.room: Room|None = None

class Room:
    def __init__(self, room_code, host_id, host_name):
        self.code = room_code
        self.host_id = host_id
        self.member_ids: List[int] = [host_id]
        self.member_names: List[str] = [host_name]
        Server.clients[host_id].room = self
    
    def add_client(self, client_id, client_name: str):
        Server.clients[client_id].room = self
        self.member_ids.append(client_id)
        self.member_names.append(client_name)

    def remove_client(self, client_id):
        Server.clients[client_id].room = None
        index = self.member_ids.index(client_id)
        self.member_ids.pop(index)
        self.member_names.pop(index)

    def get_clients(self):
        return [Server.clients[id] for id in self.member_ids]

    def get_clients_except(self, excp_id):
        return [Server.clients[id] for id in self.member_ids if id != excp_id]
    
    def send_to_clients(self, packet: Packet, exception: None|int=None):
        clients = None
        if exception is not None:
            clients = self.get_clients_except(exception) 
        else:
            clients = self.get_clients()
        
        Server.send_packet(packet, clients)

    def write_room_data(self, packet: Packet):
        packet.write_str(self.code)
        packet.write_ints(self.member_ids)
        packet.write_strs(self.member_names)

class Server:
    singleton = None
    _message_handlers = {}

    ip = '127.0.0.1'
    port = 8080

    clients = []
    socket_to_client_id = {}
    
    free_ids = []

    socket = None
    inputs = []

    def __init__(self):
        if Server.singleton:
            raise Exception("Attempted to create more than one server")
        
        Server.singleton = self

        Server.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Server.socket.bind((Server.ip, Server.port))

        Server.socket.listen(5)
        Server.inputs = [self.socket]
    
    @staticmethod
    def register_message_handler(id, func):
        if Server.singleton is None:
            Server.singleton = Server()
        Server._message_handlers[id] = func
    
    @staticmethod
    def handle_message(packet: Packet, client_id):
        if packet.msg_id not in Server._message_handlers:
            print(f"Invalid packet received with id {packet.msg_id}")
            return

        Server._message_handlers[packet.msg_id](packet, client_id)

    @staticmethod
    def loop():
        if Server.singleton is None:
            raise Exception("Attempted to start server loop, when no server has been initialised")

        while True:
            readable, _, _ = select(Server.inputs, [], Server.inputs, 0.5)

            for sock in readable:
                if sock is Server.socket:
                    conn, _ = sock.accept()

                    id = -1
                    if len(Server.free_ids) > 0:
                        id = Server.free_ids.pop()
                        Server.clients[id] = Client(id, conn)
                    else:
                        id = len(Server.clients)
                        Server.clients.append(Client(id, conn))

                    Server.socket_to_client_id[conn] = id 
                    Server.inputs.append(conn) 
                else:
                    dead = Server.resolve_packets(sock) 
                    if dead:
                        print("Terminating socket")
                        Server.remove_client(Server.socket_to_client_id[sock], False)

    
    @staticmethod
    def remove_client(client_id, shutdown_socket=True):
        sock: socket.socket = Server.clients[client_id].socket
        
        if Server.clients[client_id].room:
            Server.clients[client_id].room.remove_client(client_id)

        Server.inputs.remove(sock)
        Server.clients[client_id] = None
        Server.free_ids.append(client_id)
        Server.socket_to_client_id.pop(sock)

        if shutdown_socket:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

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
        
        Server.handle_message(packet, Server.socket_to_client_id[sock])

        return False

    @staticmethod
    # if addresses is None then it is sent to all
    def send_packet(packet, clients): 
        for client in clients:
            client.socket.send(packet.format_to_send())

class MessageHandler:
    @staticmethod
    def register(message_id):
        def decorator(function):
            Server.register_message_handler(message_id, function)
            return function
        return decorator    


class RoomManager:
    rooms = {}
                                    # PACKET FORMATS:
    REQUEST_KICK = 0                # client_id: int
    REQUEST_JOIN = 1                # room_code: str, display_name: str
    REQUEST_LEAVE = 2               # 
    REQUEST_CREATE_ROOM = 3         # display_name: str 
    RESPONSE_JOIN_SUCCESS = 4       # room_code: str, client_ids: ints, display_names: strs
    RESPONSE_LEAVE_SUCCESS = 5      #
    RESPONSE_CREATE_SUCCESS = 6     # room_code: str
    ERROR_NOT_IN_ROOM = 7           # 
    ERROR_NO_ROOM = 8               # 
    ERROR_PERMISSION = 9            # 
    ERROR_JOIN = 10                 #  
    ERROR_LEAVE = 11                # 
    RESPONSE_KICKED = 12            # 
    ERROR_IN_ROOM = 13              #
    EVENT_PLAYER_JOIN = 14          # client_id: int, display_name: str
    EVENT_PLAYER_LEAVE = 15         # client_id: int
    DATA_SYNC = 16          # length: int, (data_key: str, data_value: variant)*

    
    _valid_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    @staticmethod
    def _generate_room_id(length=10):
        return ''.join([random.choice(RoomManager._valid_chars) for _ in range(length)])


    @staticmethod
    def new_room(host_id, host_name) -> str:
        code = RoomManager._generate_room_id()
        RoomManager.rooms[code] = Room(code, host_id, host_name)
        return code


    @staticmethod
    def remove_room(room: Room):
        for id in room.member_ids:
            Server.clients[id].room = None

        RoomManager.rooms.pop(room.code)


    @staticmethod
    def handle_room_join(packet: Packet, client: Client) -> int:
        print("Handling room join")

        if client.room is not None:
            return RoomManager.ERROR_IN_ROOM

        room_code = packet.read_str()
        if room_code not in RoomManager.rooms:
            return RoomManager.ERROR_NO_ROOM
            
        room: Room = RoomManager.rooms[room_code]
        client_name = packet.read_str()

        error = room.add_client(client.id, client_name)
        if error:
            return RoomManager.ERROR_JOIN
        else:
            response_packet = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.RESPONSE_JOIN_SUCCESS)
            
            room.write_room_data(response_packet)
            Server.send_packet(response_packet, [client])

            join_packet = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.EVENT_PLAYER_JOIN)
            join_packet.write_int(client.id)
            join_packet.write_str(client_name)
            room.send_to_clients(join_packet, client.id)

        return -1


    @staticmethod
    def handle_room_leave(_: Packet, client: Client) -> int:
        print("Handling room leave")

        if client.room is None:
            return RoomManager.ERROR_NOT_IN_ROOM
        
        room = client.room
        is_host = client.room.host_id == client.id
        error = client.room.remove_client(client.id)
        if error:
            return RoomManager.ERROR_LEAVE
        else:
            response_packet = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.RESPONSE_LEAVE_SUCCESS)
            Server.send_packet(response_packet, [client])

            if is_host:
                room.send_to_clients(Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.RESPONSE_KICKED))
                RoomManager.remove_room(room)
            else:
                leave_packet = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.EVENT_PLAYER_LEAVE)
                leave_packet.write_int(client.id)

                room.send_to_clients(leave_packet)


        return -1


    @staticmethod
    def handle_create_room(packet: Packet, client: Client) -> int:
        print("Handling room create")

        if client.room is not None:
            return RoomManager.ERROR_IN_ROOM

        room_code = RoomManager.new_room(client.id, packet.read_str())

        response = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.RESPONSE_CREATE_SUCCESS)
        response.write_str(room_code)
        Server.send_packet(response, [client])
        
        return -1
        

    @staticmethod
    def handle_kick(packet: Packet, client: Client) -> int:
        print("Handling kick")

        if client.room is None:
            return RoomManager.ERROR_NOT_IN_ROOM

        if client.room.host_id != client.id:
            return RoomManager.ERROR_PERMISSION

        kick_id = packet.read_int()
        client.room.remove_client(kick_id)

        response = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.RESPONSE_KICKED)
        Server.send_packet(response, [Server.clients[kick_id]])

        leave_packet = Packet(packet_id.SERVER_ROOM_INFO).write_int(RoomManager.EVENT_PLAYER_LEAVE)
        leave_packet.write_int(client.id)

        client.room.send_to_clients(leave_packet)
        
        return -1
    
    @staticmethod
    def handle_sync_data(packet: Packet, client: Client) -> int:
        if client.room is None:
            return RoomManager.ERROR_NOT_IN_ROOM

        if client.room.host_id != client.id:
            return RoomManager.ERROR_PERMISSION

        client.room.send_to_clients(packet, client.id)

        return -1


    @staticmethod
    @MessageHandler.register(packet_id.CLIENT_ROOM_INFO)
    def handle_room_info(packet: Packet, client_id: int):
        request = packet.read_int()
        print("Handling room info request:", request)
        client = Server.clients[client_id]

        error_code = -1
        if request == RoomManager.REQUEST_JOIN:
            error_code = RoomManager.handle_room_join(packet, client)

        elif request == RoomManager.REQUEST_LEAVE:
            error_code = RoomManager.handle_room_leave(packet, client)

        elif request == RoomManager.REQUEST_CREATE_ROOM:
            error_code = RoomManager.handle_create_room(packet, client)

        elif request == RoomManager.REQUEST_KICK:
            error_code = RoomManager.handle_kick(packet, client)
        
        elif request == RoomManager.DATA_SYNC:
            error_code = RoomManager.handle_sync_data(packet, client)
        else:
            print("ERROR: Invalid room info packet")
            return

        if error_code > 0:
            packet = Packet(packet_id.SERVER_ROOM_INFO).write_int(error_code)
            Server.send_packet(packet, [client])
