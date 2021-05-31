import binascii
import hashlib
import struct
import threading
import time
from typing import List

from peer import Peer
from message import MessageType, block_header_fmt, bet_fmt
ZEROS = 19 # About 20 seconds of mining on average for this difficulty level

GENESIS_HASH = bytes("0b" + 256 * '0', "ascii")

class Block:

    def __init__(self, prev_hash, timestamp, nonce, bet_num, bets):
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.bet_num = bet_num
        self.bets = bets


class Blockchain:

    def __init__(self, peer: Peer):
        self.peer = peer
        self.blockchain = [] # type: List[Block]
        self.is_mining = False
        self.stop_mining = False

    def initial_blockchain_download(self):
        if len(self.peer.peers) == 0:
            # If I am the first node in the network
            self.restart_mining()
        else:
            # otherwise sync from other nodes
            req = struct.pack('I', MessageType.IBD_REQUEST)
            self.peer.register_msg_handler(MessageType.IBD_RESPONSE, self.ibd_response_handler)
            self.peer.send_signed_data(req)
            print("[INFO] IBD Request sent")

    def ibd_response_handler(self, data, src):
        temp_blockchain = []
        prev_hash = GENESIS_HASH
        start = struct.calcsize("I") # message type
        hdr_size = struct.calcsize(block_header_fmt)
        while start < len(data):
            if not self.verify_header(prev_hash, data[:hdr_size]):
                print("ibd: Header verification failed")
                break
            else:
                nbytes, block = self._receive_block(prev_hash, data[start:])
                print("Received IBD block of", nbytes, "bytes")
                start += nbytes
                prev_hash = block.prev_hash
                temp_blockchain.append(block)
        if len(self.blockchain) == 0 or len(temp_blockchain) > len(self.blockchain):
            print("Finished IBM from", src)
            self.blockchain = temp_blockchain
            self.restart_mining()

    def restart_mining(self):
        if self.is_mining:
            self.stop_mining = True
            self.mining_thread.join()
            self.stop_mining = False
            self.mining_thread = threading.Thread(target=self.mining, args=())
            self.mining_thread.start()
        else:
            self.mining_thread = threading.Thread(target=self.mining, args=())
            self.is_mining = True
            self.mining_thread.start()


    def _receive_block(self, prev_hash, data):
        hdr_size = struct.calcsize(block_header_fmt)
        nbytes = hdr_size
        prev_hash, timestamp, nonce, bet_num = struct.unpack_from(block_header_fmt, data)
        bets = []
        for _ in range(bet_num):
            bet = struct.unpack_from(bet_fmt, data[hdr_size:])
            bets.append(bet)
            nbytes += struct.calcsize(bet_fmt)
        return nbytes, Block(prev_hash, timestamp, nonce, bet_num, bets)

    def push_my_blockchain(self, data, src):
        response = struct.pack("I", MessageType.IBD_RESPONSE)
        for block in self.blockchain:
            response += self.add_block_bytes(block)
        self.peer.send_signed_data(response, src)
        print("Sending whole blockchain to target", src)

    def add_block_bytes(self, block):
        ret = struct.pack(block_header_fmt, block.prev_hash, block.timestamp,
                                block.nonce, block.bet_num)
        for i in range(block.bet_num):
            ret += struct.pack(bet_fmt, block.bets[i].encode("ascii"))
        return ret

    def receive_new_block(self, data, src):
        start = struct.calcsize("I") # message type
        data = data[start:] # skip message type

        hdr_size = struct.calcsize(block_header_fmt)
        if len(self.blockchain) > 0:
            prev_hash = self.calc_prev_hash(self.blockchain[-1])
        else:
            prev_hash = GENESIS_HASH
        if not self.verify_header(prev_hash, data[:hdr_size]):
            print("receive_bnew_block: Header verification failed")
            return False
        else:
            prev_hash, timestamp, nonce, bet_num = struct.unpack_from(block_header_fmt, data)
            bets = []
            for _ in range(bet_num):
                bet = struct.unpack_from(bet_fmt, data[hdr_size:])
                bets.append(bet)
            self.blockchain.append(Block(prev_hash, timestamp, nonce, bet_num, bets))
            print("Received a new block")
            self.restart_mining()

    def mining(self):
        if len(self.blockchain) > 0:
            from_block = self.blockchain[-1]
            prev_hash = self.calc_prev_hash(from_block)
        else:
            prev_hash = GENESIS_HASH
        timestamp = int(time.time())
        bet_num = 4
        nonce = 0
        while not self.stop_mining:
            nonce += 1
            print("\r[INFO] mining progress: %s" % nonce, end = "")
            header = struct.pack(block_header_fmt, prev_hash, timestamp, nonce, bet_num)
            if self.verify_nonce(header):
                print("mining succeeds.")
                # Todo: Add Bets
                bets = ["this is a sample bet", "another one", "guess", "what"]
                new_block = Block(prev_hash, timestamp, nonce, bet_num, bets)
                self.blockchain.append(new_block)
                self.broadcast_new_block(new_block)
                prev_hash, nonce, timestamp, bet_num = \
                    self.calc_prev_hash(new_block), 0, int(time.time()), 4

    def calc_prev_hash(self, block):
        header = struct.pack(block_header_fmt, block.prev_hash, block.timestamp, block.nonce, block.bet_num)
        dgst = hashlib.sha256(header).digest()
        return dgst

    def broadcast_new_block(self, block):
        request = struct.pack("I", MessageType.NEW_BLOCK)
        request += self.add_block_bytes(block)
        self.peer.send_signed_data(request)

    def verify_header(self, prev_hash, block_header):
        if struct.unpack_from("<32s", block_header) != prev_hash:
            return False
        return self.verify_nonce(block_header)

    def verify_nonce(self, block_header):
        dgst = hashlib.sha256(block_header).digest()
        bin_str = '{:0256b}'.format(int(binascii.hexlify(dgst), 16))
        if bin_str[:ZEROS] == '0' * ZEROS:
            return True
        return False

    def verify_chain(self, chain):
        pass


