import sys
import select
import time
import uuid
import threading
from typing import Dict, Any

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

    def __init__(self, id: str, origin: str, info: str, winCond: str, amt: str, expiration):
        """
        Structure of a OpenBet
        @param origin: the identifier for the peer the originally placed the bet
        @param info: a string containinng information about the event that the bet is being placed on
        @param winCond: a string with information on what outcome is the win condition of the bet
        @param amt: a string with the amount value that the bet is placed for
        """
        super().__init__()
        # this is a hack, but don't modify '0' if you don't change other code
        if id == '0':
            self.id = str(uuid.uuid1())  # random ID for each bet generated with UUID
        else:
            self.id = str(id)
        self.originator = origin
        self.event_info = info
        self.win_cond = winCond
        self.amt = amt
        self.expire = float(expiration)  # current expiration of bets is after one minute

    def __repr__(self):
        return 'open|' + self.id + "|" + self.originator + "|" + self.event_info + "|"\
                    + self.win_cond + "|" + self.amt + "|" + str(self.expire) + "|"


class ClosedBet(Bet):

    def __init__(self, id, caller):
        """
        Structure of a ClosedBet
        @param betId: the id identifieder for the original bet this bet is referring to
        @param caller: the identifier for the peer who is calling the bet
        """
        super().__init__()
        self.id = id
        self.caller = caller
        self.expire = float("inf")

    def __repr__(self):
        return 'closed|' + self.id + "|" + self.caller


class BetList:
    """
    BetList keeps the internal list of open bets that are avalible to be called
    BetList is updated after each sucessful 
    """
    # Type hint
    betList: Dict[str, OpenBet]

    def __init__(self, peer: Peer):
        self.peer = peer
        self.betList = {}  # Type dictionary with key:id, value, Bet
        self.currentRoundBets = []

    def receive_bets(self, data, src):
        """
        When a new is heard from it's peers, add it to the currentRoundBets
        """
        print("Receive a bet:", data[:100], "number of bytes", len(data), "from", src)
        data = data[struct.calcsize("I"):]  # skip message type field

        byte_bet, = struct.unpack_from(bet_fmt, data)
        string_bet = byte_bet.decode("utf-8")
        self.currentRoundBets.append(self.string_to_bet(string_bet))
        print("current round bets:", self.currentRoundBets)

    def collect_bets(self, n):
        """
        Gives blockchain a list of n bets from the current round to add to bloack
        """
        return_list = []

        if len(self.currentRoundBets) < n:
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
        Updates the master list of open bets
        @param updatedBets: list of string bets that are confirmed from chain
        """
        for bet in updatedBets:
            if isinstance(bet, ClosedBet):
                try:
                    self.betList.pop(bet.id)  # remove all bets that were closed
                except:
                    print(f"[ERR] {bet.id}")
            elif isinstance(bet, OpenBet):
                self.betList[bet.id] = bet  # add sucessully placed bets

        # remove expired bets
        self.betList = {k: v for k, v in self.betList.items() if not self.is_expired(v)}

    def place_bet(self, origin, info, winCond, amt, expiration):
        """
        Returns new open bet object (as a string) to peer to be braodcasted
        """
        newBet = OpenBet('0', origin, info, winCond, amt, time.time() + float(expiration) * 60)
        request = struct.pack("I", MessageType.NEW_BET)
        request += struct.pack(bet_fmt, bytes(repr(newBet), 'utf-8'))
        self.currentRoundBets.append(newBet)
        self.peer.send_signed_data(request)
        return repr(newBet)

    def call_bet(self, betId, caller):
        """
        Returns called bet bet object (as a string) to peer to be braodcasted
        """
        request = struct.pack("I", MessageType.NEW_BET)

        newClosedBet = ClosedBet(betId, caller)
        if betId not in self.betList or self.is_expired(self.betList[betId]):
            print("bet id doesn't exits or bet is expired")
            return  # check the it isn't expired

        request += struct.pack(bet_fmt, bytes(repr(newClosedBet), 'utf-8'))
        self.betList.pop(betId)
        self.currentRoundBets.append(newClosedBet)
        self.peer.send_signed_data(request)
        return repr(newClosedBet)

    def get_open_bets(self):
        """
        Returns string list of bets that are callable
        """
        open_bets = []
        for bet in self.betList.values():
            if not self.is_expired(bet) and isinstance(bet, OpenBet):
                open_bets.append({
                    "uuid": bet.id,
                    "event": bet.event_info,
                    "amount": bet.amt,
                    "expiration": bet.expire,
                    "win_condition": bet.win_cond,
                    "outcome": -1, # DUMMY, just to meet GUI expectation -- GUI doesnt need
                })
        return open_bets

    def get_user_bets(self, userId):
        """
        Returns list of bets for a given user
        @param userID: string ID of the user
        """
        userBets = []
        for bet in self.betList.values():
            if not self.is_expired(bet) and bet.originator == userId:
                userBets.append({
                    "uuid": bet.id,
                    "event": bet.event_info,
                    "amount": bet.amt,
                    "expiration": bet.expire,
                     "outcome": -1, # DUMMY, just to meet GUI expectation
                })
        return userBets

    def is_expired(self, openbet):
        return time.time() > openbet.expire

    def string_to_bet(self, stringBet):
        """
        helper function that translates from strings to bets 
        """
        strBet = stringBet.split("|")
        if strBet[0] == "open":
            return OpenBet(*strBet[1:7])
        if strBet[0] == 'closed':
            return ClosedBet(strBet[1], strBet[2])
        print(type(strBet[0]), strBet[0], repr(strBet[0]))
        raise Exception("Invalid bet", stringBet)

    def betList_ts(self, betlist):
        stringBets = []
        for bet in betlist:
            stringBets.append(struct.pack(bet_fmt, bytes(repr(bet), 'utf-8')))

        return stringBets

    def update_betlist(self, bet_strings):
        new_betlist = {}
        for bet_s in bet_strings:
            string_bet = bet_s.decode("utf-8")
            bet = self.string_to_bet(string_bet)
            if isinstance(bet, OpenBet):
                new_betlist[bet.id] = bet
            elif bet.id in new_betlist:
                new_betlist.pop(bet.id)

        self.betList = new_betlist
        print("current bet list on the blockchain:", self.betList)