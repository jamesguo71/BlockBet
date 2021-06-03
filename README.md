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

The Blockchain module is responsible for synchronizing the blockchain with peers in the network. It relies on Peer to download the existing blockchain from other nodes, and also send the blockchain it holds upon request from its peers.

This module also holds a mining thread to compute a new block based on the last block in the current blockchain. If the mining succeeds, it will collect new bets from the Bet module and put these bets on the new block and broadcast it to peers. If it receives a new valid block thorough Peer from the network, it will add this block to its blockchain and start mining afresh.

When blockchain forks occur, each peer will request and check if there's a longer blockchain in the network, and change its blockchain if so. 

Structure of a block:
```
prev_hash: 32 bytes (char)
timestamp: unsigned int (32 bit)
nonce: unsigned int (32 bit)
bet_num: number of bets in the block, unsigned int (32 bit)
bets: bet_num of bets
```

### Bet

The Bet module consists of 4 classes. The bet class with two sub classes of open bets and closed bets and a BetList class. The bet leverages the Peer for all its broadcast and recieve funcationality.

Open bet objects are bets submitted by users in the UI that have an attatched expiration time. Closed bets are bets that have been called by a user.

The BetList takes in new and called bets from the GUI and sends them out to the network. Additionally, it contains functionality to allow the GUI to get lists of all open bets or bets associated with a particualar user. The BetList also supplies the blockchain with a list of bets to put onto each sucessfully computed block.

### GUI

The GUI module allows users to see open and valid bets on the chain as well as place new bets.
