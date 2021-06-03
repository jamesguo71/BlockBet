import sys
import threading
import time

from blockchain import Blockchain
from message import MessageType
from peer import Peer
from bet import BetList


peer = Peer(sys.argv[1])

print("Threading Peer...")
pa = threading.Thread(target=peer.run, args=())
pa.start()

time.sleep(3)
chain = Blockchain(peer)
betlist = BetList(peer)
peer.register_msg_handler(MessageType.IBD_RESPONSE, chain.ibd_response_handler)
chain.initial_blockchain_download()
peer.register_msg_handler(MessageType.IBD_REQUEST, chain.push_my_blockchain)
peer.register_msg_handler(MessageType.NEW_BLOCK, chain.receive_new_block)

peer.register_msg_handler(MessageType.NEW_BET, betlist.recieve_bets)

pa.join()
#while 1:
#    line = input('..> ')
    # peer.send_signed_data(line.encode('utf-8'))
    # print(peer.get_new_message())
