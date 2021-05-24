import socket
import threading
import sys
import select
import struct
import time
from Crypto.PublicKey import RSA

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

		## Stores the time of the last peer update
		self.last_peer_check = 0

		## Stores the known peers and their associated keys if available
		self.peers = {}

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

		## Verivy that the public and private key are valid
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

			## This will hold the signatures too
			self.peers[peer] = []

			## TODO: make sure the peer isn't me
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

	def handle_client(self, fd):

		## If the first byte is a 0 then this is a PING request as a keep alive check
		## Return with 0x41414141
		data = fd.recv(4)

		try:
			value = struct.unpack('I', data)[0]
		except:
			print('[ERROR] Failed to receive data:' %(data))
			fd.close()
			return


		if value == 0:
			print('[INFO] Received a ping.')
			fd.send(struct.pack('I', 0x41414141))
		else:
			print('Unhandled option')

		fd.close()

	def update_peer_list(self):

		while(1):
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

					## This will hold the signatures too
					if peer not in self.peers:
						self.peers[peer] = []

						## TODO: make sure the peer isn't me
						print('[INFO] Added peer: %s' %(peer))

				fd.close()

				self.last_peer_check = time.time()

		return

	def run(self):

		## Create a thread to periodically do a peer list update
		peer_update = threading.Thread(target = self.update_peer_list, args = ())
		peer_update.start()

		inputs = [ self.peerfd ]

		while inputs:
			readable, writable, exceptional = select.select(inputs, [], inputs, 5)

			for r in readable:
				if r is self.peerfd:
					clientfd, client_address = self.peerfd.accept()

					## The server has a new connection waiting
					print('[INFO] Connection from a new peer: ', client_address )
					inputs.append(clientfd)
				else:
					self.handle_client(r)

					## Connections do not remain open so this is no longer needed
					## It is assumed that handle_client will close the socket
					inputs.remove(r)


p = Peer('localhost')

p.run()