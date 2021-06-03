import sys
import select
import time
import uuid
import threading

from peer import Peer
import struct
from message import MessageType, bet_fmt


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

    def __init__(self, id, origin, info, winCond, amt):
        """
        Structure of a OpenBet
        @param origin: the identifier for the peer the originally placed the bet
        @param info: a string containinng information about the event that the bet is being placed on
        @param winCond: a string with information on what outcome is the win condition of the bet
        @param amt: a string with the amount value that the bet is placed for
        """
        super().__init__()
        if id == 0:
            self.id = uuid.uuid1() #random ID for each bet generated with UUID
        else:
            self.id = id
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

    def __init__(self, peer: Peer):
        self.peer = peer
        self.betList = {} # Type dictionary with key:id, value, Bet
        self.currentRoundBets = []


    def recieve_bets(self, data):
        """
        When a new is heard from it's peers, add it to the currentRoundBets
        """
        data = data[struct.calcsize("I"):]  # skip message type field

        byte_bet = struct.unpack_from(bet_fmt, data)
        string_bet =  byte_bet.decode("utf-8") 
        self.currentRoundBets.append(self.string_to_bet(string_bet))
     

    def collect_bets(self, n):
        return_list = []

        if len(self.currentRoundBets < n):
            return_list = self.betList_ts(self.currentRoundBets)
            self.update_bets(self.currentRoundBets)
            self.currentRoundBets = []
        else:
            return_list = self.betList_ts(self.currentRoundBets[0:n])
            self.update_bets(self.currentRoundBets[0:n])
            self.currentRoundBets = self.currentRoundBets[n:]

        
        return return_list
        

    def update_bets(self, updatedBets):
        """
        @param updatedBets: list of string bets that are confirmed from chain
        """
        for bet in updatedBets:
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
        newBet = OpenBet(0, origin, info, winCond, amt)
        request = struct.pack("I", MessageType.NEW_BET)
        request += struct.pack(bet_fmt, bytes(repr(newBet)), 'utf-8')
        self.peer.send_signed_data(request)

        self.currentRoundBets.append(newBet)
        return repr(newBet)
        

    def call_bet(self, betId, caller):
        """
        Returns called bet bet object (as a string) to peer to be braodcasted
        """
        request = struct.pack("I", MessageType.NEW_BET)

        newClosedBet = ClosedBet(betId, caller)
        if betId not in self.betList or self.is_expired(self.betList[betId]):
            return    #check the it isn't expired
        else:
            request += struct.pack(bet_fmt, bytes(repr(newClosedBet)), 'utf-8')

        self.peer.send_signed_data(request)

        self.currentRoundBets.append(newClosedBet)
        return repr(newClosedBet)


    def get_open_bets(self):
        """
        Returns string list of bets that are callable
        """
        open_bets = []
        for bet in self.betList.values():
            open_bets.append(repr(bet))

        return open_bets


    def get_user_bets(self, userId):
        """
        Returns list of bets for a given user
        @param userID: string ID of the user
        """
        userBets = []
        for bet in self.betList.values():
                 if bet.originator == userId:
                        userBets.append(repr(bet))
        return userBets


    def is_expired(self, openbet):
        return time.time() > openbet.expire

    
    def string_to_bet(self, stringBet):
        """
        helper function that translates from strings to bets 
        """
        strBet = stringBet.split( )
        if strBet[0].equals('open'):
            return OpenBet(strBet[1], strBet[2], strBet[3], strBet[4], strBet[5])
        if strBet[0].equals('closed'):     
            return ClosedBet(strBet[1], strBet[2]) 

    def betList_ts(self, betlist):
        stringBets = []
        for bet in betlist:
            stringBets.append(bytes(repr(bet)), 'utf-8')

        return stringBets


