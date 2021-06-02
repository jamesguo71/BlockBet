import socket
import threading
import sys
import select
import struct
import time
import uuid


""" The Bet module has

    BetList collects (as a end reciever) bets from the network and the current Node.
	whichever nodes successfully computes the next valid block can have the bets they have received put on the block (confirmed). 
	The other bets are discarded.

    Bets = 'trasactions'
        #open bets - bet id,  bet originator, bet event info, bet win condition, bet amount, bet expiration
        #closed bet - which original bet it's referring to, bet caller person, 
    Each block has list of bets with both open bets and closed bets
"""


class Bet:

     def __init__(self):
        """
        Structure of a Bet
        @param header: a header so it can be read that this is a bet
        """
        self.header = 'bet'  # Used to identify the broadcast message is a Bet
      

class OpenBet(Bet):

     def __init__(self, origin, info, winCond, amt):
        """
        Structure of a OpenBet
        @params
        """
        super().__init__()
        self.id = uuid.uuid1()
        self.originator = origin
        self.event_info = info
        self.win_cond = winCond
        self.amt = amt
        self.expire = time.time() + 60 # current expiration of bets is after one minute
      

class ClosedBet(Bet):

     def __init__(self, bet, caller):
        """
        Structure of a ClosedBet
        @params
        """
        super().__init__()
        self.betId = bet
        self.caller = caller
      

class BetList:  

    def __init__(self):
        """
        @param betList: list of open bets
        """
        self.betList = {} # Type dictionary with key:id, value, Bet
        self.expireThread = Thread(target = self.removeExpire, args = ())
        self.expireThread.start()

    #remove expired bets
    # def removeExpire(self):
    #     while True:
    #         for bet in self.betList.items():
    #             if is_expired(bet[1]):
    #                 self.betList.pop(bet[0])


    def update_bets(self, updatedBets):
        for bet in updatedBets:
            if isinstance(bet, ClosedBet):
                self.betList.pop(bet.betId)
            elif isinstance(bet, OpenBet):
                 self.betlist[bet.id] = bet

        #remove expired here??? Ask
        for bet in self.betList.items():
                 if is_expired(bet[1]):
                     self.betList.pop(bet[0])


    def place_bet(self, origin, info, winCond, amt):
        return OpenBet(origin, info, winCond, amt)
        
    def get_open_bets(self):
       return self.betList.values()

    def call_bet(self, betId, caller):
        ClosedBet(betId, caller)

    def is_expired(self, openbet):
        return time.time() > openbet.expire
            
