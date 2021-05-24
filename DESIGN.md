# Product Design
### Fei Guo, Danielle Fang, Angus Emmett, John Berry 
### May 2021



## Overview

The Client Node starts, and lets the Peer connect to the Tracker to know other Nodes’ addresses and connect to them. Then the game starts and Client can choose to put a bet or not. Meanwhile, Client starts to synchronize the Blockchain that has all the game records. After the synchronization, Client can start the mining as well (compute the next valid block). If anyone successfully mined a block, then this round of game is done, and this block is broadcast to other Nodes.



## Modules

### Tracker

The tracker maintains a list of active nodes including their public keys so that signatures can be verified. A few necessary functions: add, delete, listing, query.

### Peer
Peer connects to Tracker to add itself as a node and to get information about active peers. 
Then it behaves like an “overlay” node. The main functionality it provides is to talk with peers, for example, to synchronize the Blockchain, and send/receive bets.

### Bet

Active nodes in the network can bet against each other. The Bet module collects bets from the network and the current Node.  

Unconfirmed bets should be synchronized, but this can be done on a “best-effort” basis, which means, whichever nodes successfully computes the next valid block can have the bets they have received put on the block (confirmed). The other bets are discarded.

### Blockchain

General idea about Blockchain:

It used Peer to synchronize the blockchain with other nodes. 
It also provides the “mining” function, which can compute the next valid block. (Or this can be put into a Miner module. )
We can define a valid block similarly to Bitcoin, e.g, find a nonce for the header that makes the shasum of the header to have some number of zeros. The header of a block has no information about the bets. The bets are in the “payload” of the block in a sense.
If some Node successfully computes a valid block, it can add the unconfirmed bets to the block. It also puts its “identifier” down on the block.
Verification of new blocks received from the network can be done here as well

More specifically, here is what I think about the structure of a block:
- prev hash
- height
- timestamp
- nonce
- miner id
- bets

(what about the structure of a bet?)

Methods that Blockchain should provide:
- initial blockchain download, for syncing existing blockchain from the network
- send the whole blockchain to a node, so that its peers can do blockchain initial sync when they start for the first time.  
- receive newly-mined block from network, verify the block, if OK, then update.
- mine the next valid block. On success, notify Client and let Client update the block with the current bets pool before broadcasting.


### Node/Client

The client behaves like a chat room participant. But the messages it receives are about, for example: updates of the Blockchain, its own mining success, received bets from other nodes, the betting result of the last block. It also asks the user if they want to put a bet in this round or not. There also should be some statistics for the user, like how many bets they have won / lost, how many successful minings they have done, and current height of the blockchain. Maybe the client also displays the details of the last game, like which users were betting, the shasum of the last block, etc.

More specifically, 
- initialize Peer, Blockchain and Bet
- start Peer, which talks to peers through Tracker in a new thread
    - when Peer learns of changes in Tracker, print out these messages

- Blockchain starts IBD (Initial Block Downloading) from Peer in a new thread
    - when done, start mining.
    - When mining succeeds, collect bets from Bet and broadcast the block to the network
- Client registers Blockchain's handler for the event that:
     - Peer receives a new valid block from the network
     - Peer receives a request to sync the entire blockchain 

- On Client start, Bet first syncs the current bet pool from other nodes. Then it waits for new bets from the network. 
- Client should register Bet's handler for new bet from the network event.
- Client asks users if they want to put a bet in this round. If so, Bet collects this bet and broadcast it to the network.  

- Show some statistics, maybe through a global Stat object

Client is also responsible for the Crypto setup. See this comment:  

The client will need its own public/private key pair for signing. When the client sends out its bet to the network the data sent needs to be a concatenation of the data + signature of the data. All the nodes then need to mine based on both the data and the signature. We could have the tracker be like a key repository. When a client connects, it sends its information along with a public key. The peers can verify the signed data by retrieving the key from the tracker if they don’t have a copy themselves.



