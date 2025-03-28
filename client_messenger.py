from packet import Packet
import packet_id
from networking_client import *
import threading
import rsa

encrypted_communication = False

server_public_key = None
server_n = None

client_private_key, client_public_key, client_n = rsa.generate_keys() 
if client_private_key is None or client_n is None:
    exit(0)

print(f"Client keys: {client_private_key} {client_public_key} {client_n}")

Client()

@MessageHandler.register(packet_id.SERVER_KEYS)
def handle_keys(packet: Packet):
    global server_public_key, server_n
    server_public_key, server_n = packet.read_ints()

    print("Received server encryption key!", server_public_key, server_n)

@MessageHandler.register(packet_id.SERVER_MESSAGE)
def handle_message(packet: Packet):
    print("Bank: " + packet.read_str())

@MessageHandler.register(packet_id.SERVER_ENCRYPTED_MESSAGE)
def handle_encrypted_message(packet: Packet):
    print("Bank: " + rsa.decrypt_string(packet.read(packet.read_int()), client_private_key, client_n))

server_thread = threading.Thread(target=Client.loop)
server_thread.start()

Client.send_packet(Packet(packet_id.CLIENT_KEYS).write_ints([client_public_key, client_n]))

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
        msg_bytes = rsa.encrypt_string(msg, server_public_key, server_n)
        Client.send_packet(
            Packet(packet_id.CLIENT_ENCRYPTED_MESSAGE).write_int(len(msg_bytes)).write(msg_bytes),
        )
    else:
        Client.send_packet(
            Packet(packet_id.CLIENT_MESSAGE).write_str(msg),
        )
