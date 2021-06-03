# CS60 Spring 2021, Final Project

# Overview

## Running Things

Since this is a gui application we ran it from our laptops while connected to the VPN via GlobalProtect. Once connected you can find your IP address via the GlobalProtect menu. Once found, on person must run Tracker and let everyone know their IP address. Then Peers can be connected using that IP address as the first argument on the command line.

## Good Inputs

### Running Tracker

Tracker is fairly straightforward and only needs three ports available to execute:

```
python3 tracker.py
[INFO] Tracker listening on port: 60666
[INFO] Tracker listening on port: 60667
[INFO] Tracker listening on port: 60668
```

### Connecting a peer

```
python3 client.py localhost
[INFO] Tracker accepted the public key
[INFO] Peer listening on port: 60668
Threading Peer...
[INFO] Connection from Tracker / a new peer:  ('127.0.0.1', 52334)
[INFO] Received a ping.
[INFO] Updating the peer list
```

### Adding a Bet

In the GUI fill out each of the text boxes with data. i.e.

```
Bet Event: The Next Sports Bowl
Win Condition: The team from my home town
Bet Amount: 100
Bet Expiration: 60
```

Click ``Send Bet``

### Viewing available bets

Click ``Refresh``

After the bet has been mined it should appear in the window.

### Navigating the bet window

Send multiple bets as described and wait for them to appear via refreshing.

Using the mouse select each to confirm that their data is correct.

### Accepting a bet

In the bet window select an available bet.

Click ``Accept Bet``

The bet should be removed from the list and sent to the block chain as closed.

## Bad inputs

### Invalid IP for Tracker

```
python3 client.py 999.999.999.999
[ERROR] Failed to connect to 999.999.999.999: 60666
```

### Missing public key

```
python3 client.py localhost
[ERROR] Failed to open public key: public.pem

```

### Missing private key

```
python3 client.py localhost
[ERROR] Failed to open private key: private.pem
```

### Invalid public key

```
echo aaa >> public.pem
python3 client.py localhost
[ERROR] Invalid public key
```

### Invalid private key

```
echo 'aaaa' > private.pem
python3 client.py localhost
[ERROR] Invalid private key

```

### Send Bet while missing inputs

Nothing should happen since if any of them are empty it ignores the click.

### Bets on the same event

Submit multiple bets with identical Bet Event values then wait for the blocks to be mined.

Both will show up and acceptable.

