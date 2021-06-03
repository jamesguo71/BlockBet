import binascii
import hashlib
import logging
import struct
import threading
import time
import random
from typing import List

from bet import BetList
from peer import Peer
from message import MessageType, block_header_fmt, bet_fmt, hash_header_fmt

# Hoping for 20secs per block with this difficulty level, but depends on host machines
ZEROS_NUM = 22
# The hash expected to appear in the first REAL block of the blockchain
GENESIS_HASH = hashlib.sha256(bytes("0b" + 256 * '0', "ascii")).digest()

class Block:

    def __init__(self, prev_hash, timestamp, nonce, bet_num, bets):
        """
        Structure of a Block.
        @param prev_hash: a 32-byte sha256 hash of the header of previous block
        @param timestamp: a int, typically generated with int(time.time)
        @param nonce: a number that makes the hash of the current block's header have ZEROS_NUM of zeros in the beginning
        @param bet_num: number of bets held in the block
        @param bets: specific bets, each of type `bytes`
        """
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.bet_num = bet_num
        self.bets = bets


class Blockchain:

    def __init__(self, peer: Peer, betlist: BetList):
        self.peer = peer
        self.betlist = betlist
        self.blockchain = []  # type: List[Block]
        self.mining_thread = None # Just a placeholder, will be initialized later
        self.is_mining = False # To identify if mining already begun
        self.stop_mining = False # Used to stop a previously started mining thread

    def initial_blockchain_download(self):
        if len(self.peer.peers) == 0:
            # If I am the first node in the network
            self.restart_mining()
        else:
            # otherwise sync from other nodes
            self.whole_blockchain_request()

    def whole_blockchain_request(self):
        """
        Send requests to the network to download whole blockchain from peers
        """
        req = struct.pack('I', MessageType.IBD_REQUEST)
        self.peer.send_signed_data(req)
        print("[IBD] IBD Request sent")

    def ibd_response_handler(self, data, src):
        """
        Initial blockchain download handler, or whole blockchain handler.
        Used when initially syncing blockchain with other peers,
        or when a different blockchain (a fork) seems to appear
        @param data: data received by Peer module
        @param src: which peer sent the data
        """
        temp_blockchain = []
        prev_hash = GENESIS_HASH
        start = struct.calcsize("I")  # message type
        hdr_size = struct.calcsize(hash_header_fmt)
        while start < len(data):
            # Received data contains the whole blockchain, so we loop over it to get all the blocks
            if not self.verify_header(prev_hash, data[start:start + hdr_size]):
                print("[IBD] ibd: Header verification failed")
                break
            else:
                n_bytes, block = self._receive_block(data[start:])
                print("[IBD] Received IBD block of", n_bytes, "bytes")
                start += n_bytes
                prev_hash = self.calc_prev_hash(block)
                temp_blockchain.append(block)
        if len(self.blockchain) == 0 or len(temp_blockchain) > len(self.blockchain):
            # Only if the nodes' blockchain is zero length, or the received blockchain is longer
            print("[IBD] Finished IBD from", src)
            self.blockchain = temp_blockchain
            self.on_blockchain_changed()
            self.restart_mining()

    @staticmethod
    def _receive_block(data):
        # This is just a helper function for ibd_response_handler
        hdr_size = struct.calcsize(block_header_fmt)
        n_bytes = hdr_size
        prev_hash, timestamp, nonce, bet_num = struct.unpack_from(block_header_fmt, data)
        bets = []
        for _ in range(bet_num):
            bet, = struct.unpack_from(bet_fmt, data[hdr_size:])
            bets.append(bet)
            n_bytes += struct.calcsize(bet_fmt)
        return n_bytes, Block(prev_hash, timestamp, nonce, bet_num, bets)

    def restart_mining(self):
        """
        Mining can be started anytime, but when a new valid block received,
        or the node's mining succeeds, restart the mining process.
        """
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

    def push_my_blockchain(self, data, src):
        """
        When a blockchain syncing request received from the network, the node pushes
        its whole blockchain to that peer
        """
        # assert struct.unpack_from("I", data) == MessageType.IBD_REQUEST
        response = struct.pack("I", MessageType.IBD_RESPONSE)
        for block in self.blockchain:
            response += self.add_block_bytes(block)
        print("[IBD] Sending whole blockchain to target", src)
        self.peer.send_signed_data(response, src)

    @staticmethod
    def add_block_bytes(block):
        """
        A helper function to transform an Block object to bytes
        """
        ret = struct.pack(block_header_fmt, block.prev_hash, block.timestamp,
                          block.nonce, block.bet_num)
        for i in range(block.bet_num):
            ret += struct.pack(bet_fmt, block.bets[i])
        return ret

    def receive_new_block(self, data, src):
        """
        When a new block computed by peers received, the node checks its validity
        and add to its blockchain, then restart mining
        """
        data = data[struct.calcsize("I"):]  # skip message type field

        hash_hdr_size = struct.calcsize(hash_header_fmt)
        if len(self.blockchain) > 0:
            prev_hash = self.calc_prev_hash(self.blockchain[-1])
        else:
            prev_hash = GENESIS_HASH
        if not self.verify_header(prev_hash, data[:hash_hdr_size]):
            print("[INFO] receive_new_block: Header verification failed")
            # download peers' block chain to check if there's a longer blockchain fork
            self.whole_blockchain_request()
        else:
            hdr_size = struct.calcsize(block_header_fmt)
            prev_hash, timestamp, nonce, bet_num = struct.unpack_from(block_header_fmt, data)
            bets = []
            for _ in range(bet_num):
                bet, = struct.unpack_from(bet_fmt, data[hdr_size:])
                bets.append(bet)
            new_block = Block(prev_hash, timestamp, nonce, bet_num, bets)
            self.blockchain.append(new_block)
            self.on_blockchain_changed()
            print("[SUCCESS] Received a new valid block from ", src)
            print("[INFO] Current blockchain height:", len(self.blockchain))
            print("[INFO] Nonces of last 5 blocks:", [str(block.nonce) for block in self.blockchain[-5:]])
            self.restart_mining()

    def mining(self):
        if len(self.blockchain) > 0:
            from_block = self.blockchain[-1]
            prev_hash = self.calc_prev_hash(from_block)
        else:
            prev_hash = GENESIS_HASH
        while not self.stop_mining:
            # use random nonce to increase the chance of a blockchain fork
            timestamp = int(time.time())
            nonce = random.randint(1, 10**9)
            header = struct.pack(hash_header_fmt, prev_hash, timestamp, nonce)
            if self.verify_nonce(header):
                bets = self.betlist.collect_bets(10)
                bet_num = len(bets)
                new_block = Block(prev_hash, timestamp, nonce, bet_num, bets)
                self.blockchain.append(new_block)
                print("[INFO] Mining succeeded. Current blockchain height:", len(self.blockchain))
                print("[INFO] Nonces of last 5 blocks:", [str(block.nonce) for block in self.blockchain[-5:]])
                self.broadcast_new_block(new_block)
                self.on_blockchain_changed()
                prev_hash = self.calc_prev_hash(new_block)

    @staticmethod
    def calc_prev_hash(block):
        # Calculate the header hash of a block
        header = struct.pack(hash_header_fmt, block.prev_hash,
                             block.timestamp, block.nonce)
        dgst = hashlib.sha256(header).digest()
        return dgst

    def broadcast_new_block(self, block):
        request = struct.pack("I", MessageType.NEW_BLOCK)
        request += self.add_block_bytes(block)
        self.peer.send_signed_data(request)

    def verify_header(self, prev_hash, block_header):
        logging.debug("prev_hash", prev_hash)
        logging.debug("block_header", block_header)
        logging.debug("unpacked", struct.unpack_from("<32s", block_header))
        if struct.unpack_from("<32s", block_header)[0] != prev_hash:
            return False
        logging.debug("hash ok, then nonce")
        return self.verify_nonce(block_header)

    @staticmethod
    def verify_nonce(block_header):
        dgst = hashlib.sha256(block_header).digest()
        bin_str = '{:0256b}'.format(int(binascii.hexlify(dgst), 16))
        if bin_str[:ZEROS_NUM] == '0' * ZEROS_NUM:
            return True
        return False

    def on_blockchain_changed(self):
        self.betlist.update_betlist([bet for block in self.blockchain for bet in block.bets])

