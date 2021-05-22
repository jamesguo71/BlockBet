import socket
import threading
import sys
import select
from Crypto.PublicKey import RSA 
from Crypto.Signature import PKCS1_v1_5 
from Crypto.Hash import SHA256

class Tracker:
	"""This class is the main tracker class used to manage
		peers in the blockchain network. It will store public keys too."""

	def __init__(self, peer_port=60666, sig_port=60667):
		""" Set up the listening port and initialize the peer variable.
			peer_port is used for new peers to connect to the network and
				provide their signature.
			sig_port is used for peers to connect and send a request for
				the public key of a specific peer. If the tracker has one
				then it will respond in kind otherwise it will responde with
				the string 'Unknown'. Signatures will be stored based upon the
				hostname of the peer.
		"""

		self.peerfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.peerfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.peerfd.bind(('', peer_port))
		except socket.error as m:
			print('Bind failed. ', m)
			sys.exit()

		## Start the listener
		self.peerfd.listen(10)

		print('[INFO] Tracker listening on port: %d' %(peer_port))

		self.sigfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sigfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.sigfd.bind(('', sig_port))
		except socket.error as m:
			print('Bind failed. ', m)
			sys.exit()

		## Start the listener
		self.sigfd.listen(10)

		print('[INFO] Tracker listening on port: %d' %(sig_port))

		self.registered = {}

		## Dict for clients registering as peers
		self.peers = []

		## Dict for clients requesting a signature
		self.sigs = []

	def run(self):

		inputs = [ self.peerfd, self.sigfd ]

		while inputs:
			readable, writable, exceptional = select.select(inputs, [], inputs)

			for r in readable:
				if r is self.peerfd:
					clientfd, client_address = self.peerfd.accept()

					## The server has a new connection waiting
					print('[INFO] Connection from a new peer: ', client_address )
					inputs.append(clientfd)

					self.peers.append(clientfd)
				elif r is self.sigfd:
					clientfd, client_address = self.sigfd.accept()

					print('[INFO] Connection from a new sig request: ', client_address )

					inputs.append(clientfd)
					self.sigs.append(clientfd)
				else:					
					## There are two possibilities. If this is a peer then they will
					## 	send their signature otherwise it is an existing peer searching
					##  for a public key.
					data = r.recv(1024).rstrip(b'\n')

					if data:
						## Check if the receiver is in the peer list. If so then the
						## 	data should be a signature
						if r in self.peers:
							try:
								print(data)
								rsakey = RSA.importKey(data)
							except:
								## If it fails then the key is invalid. Respond with 'Rejected' and drop the connection
								r.send(b'Rejected')
								r.close()
								self.peers.remove(r)
								inputs.remove(r)
						elif r in self.sigs:
							print('Request for %s' %(data))
							r.send(b'HERE\n')
							r.close()
							self.sigs.remove(r)
							inputs.remove(r)

					else:
						inputs.remove(r)


p = Tracker()

p.run()