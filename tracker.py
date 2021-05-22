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

	def __init__(self, peer_port=60666, sig_port=60667, list_port=60668):
		""" Set up the listening port and initialize the peer variable.
			peer_port is used for new peers to connect to the network and
				provide their signature.
			sig_port is used for peers to connect and send a request for
				the public key of a specific peer. If the tracker has one
				then it will respond in kind otherwise it will responde with
				the string 'Unknown'. Signatures will be stored based upon the
				hostname of the peer.
			list_port is used for peers to connect and request the list of
				peers in the network. If the requesting peer is not in the
				registered list then Rejected will be returned otherwise,
				the list of known nodes will be returned.
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

		self.listfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.listfd.bind(('', list_port))
		except socket.error as m:
			print('Bind failed. ', m)
			sys.exit()

		## Start the listener
		self.listfd.listen(10)

		print('[INFO] Tracker listening on port: %d' %(list_port))

		self.registered = {}

		## Dict for clients registering as peers
		self.peers = []

		## Dict for clients requesting a signature
		self.sigs = []

		## Dict for clients requesting a peer list
		self.lists = []
	def run(self):

		inputs = [ self.peerfd, self.sigfd, self.listfd ]

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
				elif r is self.listfd:
					clientfd, client_address = self.listfd.accept()

					print('[INFO] Connection from a new list request: ', client_address )

					host, port = clientfd.getpeername()

					if host not in self.registered:
						r.send(b'Rejected')
						r.close()

					## Create a list of registered peers
					info = ''

					for p in self.registered:
						info += p + '\n'

					clientfd.send(info.encode('utf-8'))
					clientfd.close()
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

								continue

							## If this point is reached then the key is valid and we can accept the client as a peer
							r.send(b'Accepted')

							host, port = r.getpeername()
							self.registered[host] = {'signature': data}

							print(self.registered)

							r.close()
							self.peers.remove(r)
							inputs.remove(r)

							print(self.registered)
						elif r in self.sigs:
							## If the requesting peer is not registered then response is Rejected
							host, port = r.getpeername()

							if host not in self.registered:
								r.send(b'Permission Denied')
								r.close()
								self.sigs.remove(r)
								inputs.remove(r)

								continue

							print('Peer requested signature for %s' %(data))
							
							## When returned from getpeername() the address is not store as bytes
							data = data.decode('utf-8')

							if data not in self.registered:
								r.send(b'Unknown')
							else:
								r.send(self.registered[data]['signature'])

							r.close()
							self.sigs.remove(r)
							inputs.remove(r)

					else:
						inputs.remove(r)


p = Tracker()

p.run()