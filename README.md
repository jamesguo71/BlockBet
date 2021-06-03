# CS60 Spring 2021
# Project Title: BlockBet
## The Gamblers

## Team members: Fei Guo, Danielle Fang, Angus Emmett, John Berry 

## Components

### P2P Networking

The underlying peer-to-peer networking is handled by the components we call Tracker and Peer. Peers register with the Tracker and then communicate with the other peers directly.

#### Tracker

Tracker has 3 primary purposes

1. Maintain the available peer list with public keys
2. Provide the peer list when requested
3. Provide signatures of peers when requested.

When Tracker starts up is begins listening on three ports which default to 60666, 60667, and 60668. When a peer wants to register to the network it must connect to port 60666 and send a valid public key. If the key is valid Tracker will respond with "Accepted" and add the peer to the list. Otherwise it will respond with "Rejected" and drop the request.

To get an updated peer list a peer connects to port 60667 and if the requesting peer is a valid peer in Trackers list then it will respond with the list of all live peers.

To retrieve a signature of a peer, a client connects to port 60668 and sends the IP address of the peer whose key it needs. The requesting peer must be registered with tracker or the request will be denied. If the request is valid the signature is returned otherwise the string "Unknown" is returned.

Periodically Tracker pings all peers to determine their liveness.

#### Peer

When a peer starts up it immediately connects to Tracker and sends its public key. Once accepted it connects again to retrieve a list of peers in the network. Finally, peer opens a port on which it will receive data from peers and ping requests from Tracker.

When a new connection is accepted the peer checks if it has the signature for the sender. If not it requests the key from Tracker. Once the signature is verified Peer places the new message on the queue for the upper layers to pull and process.

If a peer receives a message with a size field (described later) of 0 then it assumes that the request is a PING and responds with a hex value indicating that it is alive.

#### Protocol

|Bytes |Field Name |Description|
| :--: | :--: | :--: |
| <0-1> | Data Length | Specifies the length of the data in this message|
| <2-3> | Sig Length | Specifies the length of the signature in this message |
| <DL> | Data | The data filed for this message. |
| <SL> | Signature | The signature for this message. It does not include the length fields|

### Blockchain

The Blockchain is responsible for picking the blocks out of Peer and either beginning the hash to compute a new block or adding the newly computed block to the chain. It is agnostic of the structure of the Bet data.

### Bet

The Bet module takes in new and called bets from the GUI and sends them out to the network. It also maintains a list of valid open bets that the GUI is able to call.

### GUI

The GUI module allows users to see open and valid bets on the chain as well as place new bets.
