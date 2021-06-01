import time


# Bet in form:
# 				bet = {event:string, amount:float, expriation:unixtime, uuid:int, outcome:[-1,0,1]}


def get_open_bets():
	open_bets = [
		{"uuid":0, "event":"Pigs can fly", 						"amount":110.0, "expiration":time.time() + 100, "outcome":-1},
		{"uuid":1, "event":"Cow jumps over the moon", 			"amount":102.0, "expiration":time.time() + 100, "outcome":-1},
		{"uuid":2, "event":"get 110% on project", 				"amount":220.2, "expiration":time.time() + 100, "outcome":-1},
		{"uuid":3, "event":"Apple glasses released this year", 	"amount":100.9, "expiration":time.time() + 100, "outcome":-1},
		{"uuid":4, "event":"I get RTX 3080 Ti", 				"amount":999.9, "expiration":time.time() + 100, "outcome":-1}
	]

	return open_bets


def get_pending_bets():
	pending_bets = [
		{"uuid":5, "event":"I jump high", 						"amount":110.0, "expiration":time.time() + 100, "outcome":0},
		{"uuid":6, "event":"global language", 					"amount":102.0, "expiration":time.time() + 100, "outcome":0},
		{"uuid":7, "event":"my professor is awesome", 			"amount":220.2, "expiration":time.time() + 100, "outcome":0},
	]

	return pending_bets



def get_my_bets(user_id):
	return
