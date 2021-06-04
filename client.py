import socket
import sys
import threading
import time

from blockchain import Blockchain
from message import MessageType
from peer import Peer
from bet import BetList
import gui

peer = Peer(sys.argv[1])

print("Threading Peer...")
pa = threading.Thread(target=peer.run, args=())
pa.start()

# Wait for peer to sync its peer list
time.sleep(3)

betlist = BetList(peer)
chain = Blockchain(peer, betlist)

peer.register_msg_handler(MessageType.IBD_RESPONSE, chain.ibd_response_handler)
peer.register_msg_handler(MessageType.IBD_REQUEST, chain.push_my_blockchain)
peer.register_msg_handler(MessageType.NEW_BLOCK, chain.receive_new_block)
peer.register_msg_handler(MessageType.NEW_BET, betlist.receive_bets)

chain.initial_blockchain_download()

gui.main(betlist)


# pa.join()
# while 1:
#     line = input('\r..> ')
#     print("You just put a bet:", line)
#     sys.stdout.flush()
#     betlist.place_bet(socket.gethostname(), line, "Yes!", "50", time.time() + 120)
#     print(betlist.betList)
