import sys
import threading

from blockchain import Blockchain
from message import MessageType
from peer import Peer


peer = Peer("localhost", conn_port=int(sys.argv[1]))

print("Threading Peer...")
pa = threading.Thread(target=peer.run, args=())
pa.start()

chain = Blockchain(peer)
chain.initial_blockchain_download()
peer.register_msg_handler(MessageType.IBD_REQUEST, chain.push_my_blockchain)
peer.register_msg_handler(MessageType.NEW_BLOCK, chain.receive_new_block)

while 1:
    line = input('..> ')
    # peer.send_signed_data(line.encode('utf-8'))
    # print(peer.get_new_message())
