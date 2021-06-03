import socket
import threading
import sys
import select
from signal import signal, SIGINT
from Crypto.Signature import PKCS1_v1_5
import struct
import time
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256

""" Read from the socket until the value specified by 'u' is received
	include is used to specify if the trailing 'u' data is to be included or excluded
	from the final returned data
"""
def readuntil(s, u, include=False):
	data = b''

	while data.endswith(u) == False:
		data += s.recv(1)

	if include == False:
		data = data.rstrip(u)

	return data

class Peer:
	"""This class is the main tracker class used to manage
		peers in the blockchain network. It will store public keys too."""

	def __init__(self, tracker, tracker_port=60666, sig_port=60667, list_port=60668,
					conn_port=60669, pubkey="public.pem", privkey="private.pem" ):
		""" Connect to the tracker an announce as a new peer. Send the public key that
			will be used for signing.

			Get the list of peers and store them in the peer map
			
			tracker is the hostname or ip of the tracker server

			tracker_port is the port on which to connect and announce as a peer.

			sig_port is used for peers to connect and send a request for
				the public key of a specific peer. If the tracker has one
				then it will respond in kind otherwise it will responde with
				the string 'Unknown'. Signatures will be stored based upon the
				hostname of the peer.

			list_port is used for peers to connect and request the list of
				peers in the network. If the requesting peer is not in the
				registered list then Rejected will be returned otherwise,
				the list of known nodes will be returned.

			conn_port is used by the peer to allow the tracker and other peers to connect to it.

			pubkey is the public key file that will be sent to the tracker. Peers use
				this to validate signatures on data

			privkey will not be sent anywhere but is used to sign data sent to peers
		"""

		## Save all of the values for later
		self.tracker = tracker
		self.tracker_port = tracker_port
		self.sig_port = sig_port
		self.list_port = list_port
		self.conn_port = conn_port

		## Queue used to store validated messages from other peers
		self.message_queue = []

		## While this is 1 the ping thread will continue
		self.peer_loop = 1

		## Stores the time of the last peer update
		self.last_peer_check = 0

		## Stores the known peers and their associated keys if available
		self.peers = {}

		## get the current node's host_name so to ignore self in peer list
		self.host_name = socket.gethostbyname(socket.gethostname()).encode("ascii")

		## Store registered handlers for handling different types of msgs
		self.msg_handlers = {}

		## Open and read the public and private keys
		try:
			f = open(pubkey, 'rb')
		except:
			print('[ERROR] Failed to open public key: %s' %(pubkey))
			exit(1)

		self.pubkey = f.read()
		f.close()

		try:
			f = open(privkey, 'rb')
		except:
			print('[ERROR] Failed to open private key: %s' %(privkey))
			exit(1)

		self.privkey = f.read()
		f.close()

		## Verify that the public and private key are valid
		try:
			self.rsa_pubkey = RSA.importKey(self.pubkey)
		except:
			print('[ERROR] Invalid public key')
			exit(1)

		try:
			self.rsa_privkey = RSA.importKey(self.privkey)
		except:
			print('[ERROR] Invalid private key')
			exit(1)

		## Connect to the tracker and announce with the public key
		fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			fd.connect((self.tracker, self.tracker_port))
		except:
			print('[ERROR] Failed to connect to %s: %d' %(self.tracker, self.tracker_port))
			exit(1)

		fd.send(self.pubkey)

		response = fd.recv(1024)

		fd.close()

		if response != b'Accepted':
			print('[ERROR] Tracker did not accept the public key: %s' %response)
			exit(1)

		print('[INFO] Tracker accepted the public key')

		## Connect and git a list of peers
		fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			fd.connect((self.tracker, self.list_port))
		except:
			print('[ERROR] Failed to connect to %s: %d' %(self.tracker, self.tracker_port))
			exit(1)

		entry_count = readuntil(fd, b'\n')

		for e in range(int(entry_count)):
			peer = readuntil(fd, b'\n')

			## make sure the peer isn't me
			if peer == self.host_name:
				continue

			## This will hold the signatures too
			self.peers[peer] = {'sig': None}

			print('[INFO] Added peer: %s' %(peer))

		fd.close()

		## Set the initial peer check
		self.last_peer_check = time.time()

		## Setup the listener
		self.peerfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.peerfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.peerfd.bind(('', conn_port))
		except socket.error as m:
			print('Bind failed. ', m)
			sys.exit()

		## Start the listener
		self.peerfd.listen(10)

		print('[INFO] Peer listening on port: %d' %(list_port))

		## Set up the CTRL+C handler
		signal(SIGINT, self.handler)

		## Create a thread to periodically do a peer list update
		self.peer_update = threading.Thread(target = self.update_peer_list, args = ())
		self.peer_update.start()

	def verify_signature(self, message, signature, key):
		""" Function to verify the signature of a received message"""

		signer = PKCS1_v1_5.new(key)
		digest = SHA256.new()

		digest.update(message)

		return signer.verify(digest, signature)

	def get_peer_signature(self, peer):
		""" Connects to the tracker and requests the signature of
			the specified peer
		"""
		## If we don't know this peer then we don't need to request it
		if peer not in self.peers:
			return 1

		fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			fd.connect((self.tracker, self.sig_port))
		except:
			print('[ERROR] Failed to connect to tracker signature port: %s:%d' %(self.tracker, self.sig_port))
			return 1

		fd.send(peer)

		## get the signature length
		siglen = struct.unpack('I', fd.recv(4))[0]

		signature = fd.recv(siglen)

		fd.close()

		## Check for the failure case
		if siglen == 'Unknown':
			return 1

		## Import the key to ensure that it is valid
		try:
			rsa_pubkey = RSA.importKey(signature)
		except:
			print('[ERROR] Invalid public key')
			return 1

		self.peers[peer]['sig'] = signature

		return 0

	def handle_new_block(self, fd):
		"""
			The format for a block is:
			4 byte header = 0xdeadbeef (already read from the socket)
			2 byte length of the data
			2 byte length of the signature
			data[data_length]
			signature[sig_length]
		"""
		client = fd.getpeername()

		print('[INFO] Received a new block from: ', client)

		## read a 2-byte size field for the data length and 2-byte size field for signature length
		data_len = struct.unpack('H', fd.recv(2))[0]
		sig_len = struct.unpack('H', fd.recv(2))[0]

		data = fd.recv(data_len)
		sig = fd.recv(sig_len)

		## Do I have the signature for this peer?
		if self.get_peer_signature(client[0].encode('utf-8')):
			print('[ERROR] Failed to get a signature for the peer: %s' %client)
			return

		return

	def send_signed_data(self, data, target=None):
		""" This sends data to every peer in the list """

		### Use my private key to sign the data
		key = RSA.importKey(self.privkey)

		digest = SHA256.new()
		digest.update(data)

		sig = PKCS1_v1_5.new(key).sign(digest)

		block = struct.pack('H', len(data))
		block += struct.pack('H', len(sig))
		block += data
		block += sig

		if target is None:
			targets = self.peers
		else:
			targets = [ target ]
		
		target_copy = targets.copy()
		for p in target_copy:
			fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			try:
				fd.connect((p, self.conn_port))
			except:
				print('[ERROR] Failed to connect to %s:%d' %(p, self.conn_port))
				continue

			print("[INFO] Data sent to peer:", p)
			fd.sendall(block)

			fd.close()

		return

	def get_new_message(self):
		if len(self.message_queue) == 0:
			return None

		return self.message_queue.pop(0)

	def handle_client(self, fd):
		## If the size fields are 0 then this is a ping
		## read a 2-byte size field for the data length and 2-byte size field for signature length
		try:
			data_len = struct.unpack('H', fd.recv(2))[0]
			sig_len = struct.unpack('H', fd.recv(2))[0]
		except:
			print('[ERROR] Failed to receive data')
			fd.close()

			return

		if data_len == 0:
			print('[INFO] Received a ping.')
			fd.send(struct.pack('I', 0x41414141))
			fd.close()

			return

		## Read the data and signature
		try:
			data = fd.recv(data_len)
			sig = fd.recv(sig_len)
		except:
			print('[ERROR] Failed to receive client data')
			fd.close()

			return

		client = fd.getpeername()

		fd.close()

		print('[INFO] Received a new message from: ', client)

		## Do I have the signature for this peer?
		if self.get_peer_signature(client[0].encode('utf-8')):
			print('[ERROR] Failed to get a signature for the peer: ', client)
			return

		print('[INFO] Signature verified on new message')

		self.message_queue.append( (data, sig) )

		msg_type, = struct.unpack_from("I", data)
		print("[INFO] Received new Message of type:", msg_type)
		self.msg_handlers[msg_type](data, client[0])

		return;

	def register_msg_handler(self, msg_type, handler):
		self.msg_handlers[msg_type] = handler

	def handler(self, s, f):
		print('[INFO] Shutting down')
		self.peer_loop = 0

		self.peer_update.join()

		self.peerfd.close()

		exit(0)

	def update_peer_list(self):

		while(self.peer_loop):
			time.sleep(5)

			if time.time() - self.last_peer_check > 10:
				print('[INFO] Updating the peer list')
				## Connect and git a list of peers
				fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

				try:
					fd.connect((self.tracker, self.list_port))
				except:
					print('[ERROR] Failed to connect to %s: %d' %(self.tracker, self.tracker_port))
					return

				entry_count = readuntil(fd, b'\n')

				for e in range(int(entry_count)):
					peer = readuntil(fd, b'\n')

					## Todo: Make sure to remove a disconnected peer

					## This will hold the signatures too
					if peer not in self.peers and peer != self.host_name:
						self.peers[peer] = {'sig': None}

						print('[INFO] Added peer: %s' %(peer))

				fd.close()

				self.last_peer_check = time.time()

		return

	def run(self):
		inputs = [ self.peerfd ]

		while inputs:
			readable, writable, exceptional = select.select(inputs, [], inputs, 5)

			for r in readable:
				if r is self.peerfd:
					clientfd, client_address = self.peerfd.accept()

					## The server has a new connection waiting
					print('[INFO] Connection from Tracker / a new peer: ', client_address )
					inputs.append(clientfd)
				else:
					self.handle_client(r)

					## Connections do not remain open so this is no longer needed
					## It is assumed that handle_client will close the socket
					inputs.remove(r)


if __name__ == "__main__":
	p = Peer(sys.argv[1])

	print("THreading...")
	pa = threading.Thread(target = p.run, args = ())
	pa.start()

	while 1:
		line = input('..> ')
		p.send_signed_data(line.encode('utf-8'))
		print(p.get_new_message())
