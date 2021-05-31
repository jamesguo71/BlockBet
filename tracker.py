import socket
import threading
import sys
import select
import struct
import time
from signal import signal, SIGINT
from Crypto.PublicKey import RSA

class Tracker:
	"""This class is the main tracker class used to manage
		peers in the blockchain network. It will store public keys too."""

	def __init__(self, peer_port=60666, sig_port=60667, list_port=60668, conn_port=60669):
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

			conn_port is used by the peer to allow the tracker and other peers to connect to it.
		"""

		## Periodically to a check to make sure that the peers are still live
		self.last_ping_request = time.time()

		self.conn_port = conn_port

		## This is used to indicate that the ping thread should continue
		## If a user enters CTRL+C then this will be set to 0
		self.ping_loop = 1

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

	def handler(self, s, f):
		print('[INFO] Shutting down')
		self.ping_loop = 0

		self.peer_ping.join()

		self.peerfd.close()
		self.sigfd.close()
		self.listfd.close()

		exit(0)

	def perform_ping_check(self):
		while self.ping_loop:
			time.sleep(1)

			## Keep a list of the dead and remove them after the checks
			if time.time() - self.last_ping_request > 20:
				dead = []

				self.last_ping_request = time.time()

				## Loops through each known peer and attempts to confirm its liveness
				for peer in self.registered:
					fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

					try:
						fd.connect((peer, self.conn_port))
					except:
						## If this is hit then the peer is dead
						dead.append(peer)
						fd.close()
						continue

					fd.send(struct.pack('I', 0x00))

					try:
						d = fd.recv(4)
					except:
						dead.append(peer)
						fd.close()
						continue

					try:
						value = struct.unpack('I', d)[0]
					except:
						print('[ERROR] Invalid number of bytes received')
						dead.append(peer)
						fd.close()
						continue

					if value != 0x41414141:
						print('[ERROR] Invalid PING response from: %s' %peer)
						dead.append(peer)

					fd.close()


				for peer in dead:
					print('[INFO] Removing %s as peer' %(peer))
					self.registered.pop(peer)

		return

	def run(self):
		## Create a thread to periodically ping peers
		self.peer_ping = threading.Thread(target = self.perform_ping_check, args = ())
		self.peer_ping.start()

		## Set up the CTRL+C handler
		signal(SIGINT, self.handler)

		inputs = [ self.peerfd, self.sigfd, self.listfd ]

		while inputs:
			readable, writable, exceptional = select.select(inputs, [], inputs, 10)

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

					print("ADDED sig client: ", clientfd)

					inputs.append(clientfd)
					self.sigs.append(clientfd)
				elif r is self.listfd:
					clientfd, client_address = self.listfd.accept()

					print('[INFO] Connection from a new list request: ', client_address )

					host, port = clientfd.getpeername()

					if host not in self.registered:
						try:
							clientfd.send(b'Rejected')
						except:
							print('[INFO] Client disconnected early')
						clientfd.close()
						continue

					## Create a list of registered peers
					## First let the peer know how many to expect
					info = str(len(self.registered)) + '\n'

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
								rsakey = RSA.importKey(data)
							except:
								## If it fails then the key is invalid. Respond with 'Rejected' and drop the connection
								try:
									r.send(b'Rejected')
								except:
									print('[INFO] Client disconnected before sending key rejection')

								r.close()
								self.peers.remove(r)
								inputs.remove(r)

								continue

							## If this point is reached then the key is valid and we can accept the client as a peer
							try:
								r.send(b'Accepted')
							except:
								print('[INFO] Client disconnected before sending key acception')
								r.close()
								self.peers.remove(r)
								inputs.remove(r)

								continue

							try:
								host, port = r.getpeername()
							except:
								print('[ERROR] Client disconnected too soon')
								r.close()
								self.peers.remove(r)
								inputs.remove(r)

								continue

							self.registered[host] = {'signature': data}

							r.close()
							self.peers.remove(r)
							inputs.remove(r)

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
								r.send(struct.pack('I', 7))
								r.send(b'Unknown')
								print("Unknown sent.")
							else:
								r.send(struct.pack('I', len(self.registered[data]['signature'])))
								r.send(self.registered[data]['signature'])
								print("Signature sent")

							r.close()
							self.sigs.remove(r)
							inputs.remove(r)

					else:
						if r in self.sigs:
							self.sigs.remove(r)
						elif r in self.peers:
							self.peers.remove(r)

						inputs.remove(r)

p = Tracker()

p.run()
