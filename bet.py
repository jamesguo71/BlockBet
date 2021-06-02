import socket
import threading
import sys
import select
import struct
import time
import uuid
import threading


class Bet:
    """
    Bet is the parent class object with header identifying it as such
    """
    def __init__(self):
        """
        Structure of a Bet
        @param header: a header so it can be read that this is a bet
        """
        self.header = 'bet'  # Used to identify the broadcast message is a Bet < do I need to change this?
      

class OpenBet(Bet):

    def __init__(self, origin, info, winCond, amt):
        """
        Structure of a OpenBet
        @param origin: the identifier for the peer the originally placed the bet
        @param info: a string containinng information about the event that the bet is being placed on
        @param winCond: a string with information on what outcome is the win condition of the bet
        @param amt: a string with the amount value that the bet is placed for
        """
        super().__init__()
        self.id = uuid.uuid1() #random ID for each bet generated with UUID
        self.originator = origin
        self.event_info = info
        self.win_cond = winCond
        self.amt = amt
        self.expire = time.time() + 60 # current expiration of bets is after one minute

    def __repr__(self):
        return repr('open ' + self.id + " " + self.originator + " " + self.event_info + " " 
        + self.win_cond + " " + self.amt)
      

class ClosedBet(Bet):

     def __init__(self, betId, caller):
        """
        Structure of a ClosedBet
        @param betId: the id identifieder for the original bet this bet is referring to
        @param caller: the identifier for the peer who is calling the bet
        """
        super().__init__()
        self.betId = betId
        self.caller = caller
    
     def __repr__(self):
        return repr('closed ' + self.betId + " " + self.caller)
      
      

class BetList:  
    """
    BetList keeps the internal list of open bets that are avalible to be called
    BetList is updated after each sucessful 
    """

    def __init__(self):
        self.betList = {} # Type dictionary with key:id, value, Bet


    def update_bets(self, updatedBets):
        """
        @param updatedBets: list of string bets that are confirmed from chain
        """

        updatedConvertedBets = []

        #convert bets into bet obejcts
        for stringBet in updatedBets:
            updatedConvertedBets.append(self.string_to_bet(stringBet))

        for bet in updatedConvertedBets:
            if isinstance(bet, ClosedBet): 
                self.betList.pop(bet.betId) #remove all bets that were closed
            elif isinstance(bet, OpenBet):
                 self.betlist[bet.id] = bet # add sucessully placed bets

        #remove expired bets
        for bet in self.betList.items():
                 if self.is_expired(bet[1]):
                     self.betList.pop(bet[0])


    def place_bet(self, origin, info, winCond, amt):
        """
        Returns new open bet object (as a string) to peer to be braodcasted
        """
        return OpenBet(origin, info, winCond, amt)
        
    def get_open_bets(self):
        """
        Returns string list of bets that are callable
        """
        return self.betList.values()

    def get_user_bets(self, userId):
        """
        Returns list of bets for a given user
        @param userID: string ID of the user
        """
        userBets = []
        for bet in self.betList.values():
                 if bet.id == userId:
                        userBets.append(bet)
        return userBets

    def call_bet(self, betId, caller):
        """
        Returns called bet bet object (as a string) to peer to be braodcasted
        """
        #check the it isn't expired
        if betId not in self.betList or self.is_expired(self.betList[betId]):
            return "Error this is not a valid open bet"
        return ClosedBet(betId, caller)

    def is_expired(self, openbet):
        return time.time() > openbet.expire
            
    def string_to_bet(self, stringBet):
        return        


