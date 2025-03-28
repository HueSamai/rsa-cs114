from networking import *
import packet_id
from packet import Packet
import threading
import rsa

encrypted_communication = False

client_public_key = None
client_n = None

server_private_key, server_public_key, server_n = rsa.generate_keys() 
if server_private_key is None or server_n is None:
    exit(0)

print(f"Server keys: {server_private_key} {server_public_key} {server_n}")

@MessageHandler.register(packet_id.CLIENT_KEYS)
def handle_keys(packet: Packet, _):
    global client_public_key,client_n
    client_public_key, client_n = packet.read_ints()

    print("Received client encryption key!", client_public_key, client_n)

    Server.send_packet(Packet(packet_id.SERVER_KEYS).write_ints([server_public_key, server_n]), Server.clients)

@MessageHandler.register(packet_id.CLIENT_MESSAGE)
def handle_message(packet: Packet, _):
    print("Customer: " + packet.read_str())

@MessageHandler.register(packet_id.CLIENT_ENCRYPTED_MESSAGE)
def handle_encrypted_message(packet: Packet, _):
    print("Customer: " + rsa.decrypt_string(packet.read(packet.read_int()), server_private_key, server_n))

server_thread = threading.Thread(target=Server.loop)
server_thread.start()


while True:
    msg = input()
    if msg == "":
        exit(0)

    if msg == "ENCRYPT":
        encrypted_communication = True
        print("Entering encrypted communication...")
        continue
    elif msg == "DECRYPT":
        encrypted_communication = False
        print("Exiting encrypted communication...")
        continue

    
    if encrypted_communication:
        msg_bytes = rsa.encrypt_string(msg, client_public_key, client_n)
        Server.send_packet(
            Packet(packet_id.SERVER_ENCRYPTED_MESSAGE).write_int(len(msg_bytes)).write(msg_bytes),
            Server.clients
        )
    else:
        Server.send_packet(
            Packet(packet_id.SERVER_MESSAGE).write_str(msg),
            Server.clients
        )
