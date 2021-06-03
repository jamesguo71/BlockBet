import PySimpleGUI as sg
from testAPI import *


def build_layout():

	td = {"auto_size_text" : False, "justification":"c"}
	th = {"font":("Helvetica", 15, "underline")}
	tb = {"font":("Helvetica", 12)}

	# --------------------------------- Define Layout ---------------------------------
	left_col = [[sg.Button('Callable Bets'), sg.Button('My Bets')],
				[sg.Listbox(values=[], enable_events=True, size=(40,20), key='-BET_LIST-')]
				]

	right_col = [	[sg.Text('Bet Event', **td, **th )],
					[sg.Text('n/a', key="-BET_EVENT-", **td, **tb)],

					[sg.Text('Win Condition', **td, **th )],
					[sg.Text('n/a', key="-BET_WIN_COND-", **td, **tb)],

					[sg.Text('Bet Value', **td,**th)],
					[sg.Text('n/a', key="-BET_VALUE-", **td, **tb)],

					[sg.Text('Bet Expiration', **td,**th)],
					[sg.Text('n/a', key="-BET_EXPIRATION-", **td, **tb)],

					[sg.Button("Accept Bet", key="-ACCEPT_BTN-")],
					[sg.Text("_" * 50)],

					[sg.Text('Make a bet', **td, **th)],
					[sg.Text("Bet Event:", justification="l"), sg.Input(key="-EVENT_INPUT-", enable_events=True)],
					[sg.Text("Bet Amount:", justification="l"), sg.Input(key="-AMOUNT_INPUT-", enable_events=True)],
					[sg.Text("Bet Expiration (mins):",justification="l"), sg.Input(key="-EXPIRATION_INPUT-", enable_events=True)],
					[sg.Button("Send Bet", key="-SEND_BTN-")]
				]

	# ----- Full layout -----
	layout = [[sg.Column(left_col, element_justification='c'), sg.VSeperator(),sg.Column(right_col, element_justification='c')]]


	# --------------------------------- Create Window ---------------------------------
	window = sg.Window('Blockchain Bet GUI', layout, resizable=True)

	return window

def event_loop(window):

	# ----- Run the Event Loop -----
	# --------------------------------- Event Loop ---------------------------------
	bet_dict = {}
	selected_bet = None
	is_on_callable = False

	while True:
		event, values = window.read()

		# ---------- Exit Event Section ----------
		if event in (sg.WIN_CLOSED, 'Exit'):
			break
		if event == sg.WIN_CLOSED or event == 'Exit':
			break

		# ---------- Input Validation Section ----------
		#Char limit check for event input
		if event == "-EVENT_INPUT-" and values["-EVENT_INPUT-"] and len(values["-EVENT_INPUT-"]) > 100:
			window["-EVENT_INPUT-"].update(values["-EVENT_INPUT-"][0:100])

		#Char limit check for amount input
		if event == "-AMOUNT_INPUT-" and values["-AMOUNT_INPUT-"] and len(values["-AMOUNT_INPUT-"]) > 10:
			window["-AMOUNT_INPUT-"].update(values["-AMOUNT_INPUT-"][0:10])

		#Char limit check for expiration input
		if event == "-EXPIRATION_INPUT-" and values["-EXPIRATION_INPUT-"] and len(values["-EXPIRATION_INPUT-"]) > 10:
			window["-EXPIRATION_INPUT-"].update(values["-EXPIRATION_INPUT-"][0:10])

		#Numbers only check for amount input
		if event == "-AMOUNT_INPUT-" and values["-AMOUNT_INPUT-"] and values["-AMOUNT_INPUT-"][-1] not in ('0123456789.-'):
			window["-AMOUNT_INPUT-"].update(values["-AMOUNT_INPUT-"][:-1])

		#Numbers only check for expiration input
		if event == "-EXPIRATION_INPUT-" and values["-EXPIRATION_INPUT-"] and values["-EXPIRATION_INPUT-"][-1] not in ('0123456789.-'):
			window["-EXPIRATION_INPUT-"].update(values["-EXPIRATION_INPUT-"][:-1])


		
		# ---------- Click Events Section ----------
		# Callable bets clicked
		if event == "Callable Bets":
			window["-ACCEPT_BTN-"].update(disabled = False)
			is_on_callable = True

			bet_dict = get_open_bets()
			open_best_list = [x["event"] for x in bet_dict]
			window['-BET_LIST-'].update(open_best_list)

		# My Bets clicked
		elif event == "My Bets":
			window["-ACCEPT_BTN-"].update(disabled = True)
			is_on_callable = False
			bet_dict = get_user_bets()
			pending_best_list = [x["event"] for x in bet_dict]
			window['-BET_LIST-'].update(pending_best_list)

		# Item in bet list clicked
		elif event == '-BET_LIST-':    # A bet was chosen from the bet box
			selected_bet = [x for x in bet_dict if x["event"] == values["-BET_LIST-"][0]][0]

			window["-BET_EVENT-"].update(selected_bet["event"])
			window["-BET_VALUE-"].update(selected_bet["amount"])
			window["-BET_EXPIRATION-"].update(selected_bet["expiration"])
			# window["-BET_WIN_COND-"].update(selected_bet["win_condition"])


		# Send Button clicked
		elif event == "-SEND_BTN-":
			window["-EVENT_INPUT-"].update("")
			window["-AMOUNT_INPUT-"].update("")
			window["-EXPIRATION_INPUT-"].update("")

		# Accept bet button clicked
		elif event == "-ACCEPT_BTN-":
			if selected_bet != None and is_on_callable:
				accept_bet(selected_bet["uuid"])
				bet_dict = get_open_bets()
				open_best_list = [x["event"] for x in bet_dict]
				window['-BET_LIST-'].update(open_best_list)


		print(event, values)



def bet_strings_to_dicts(bet_list):
	bets = []
	for b in bet_list:
		bl = b.split(" ")
		if bl[0] != "open":
			continue

		bd = {
				"uuid": bl[1],
				"originator": bl[2],
				"event":bl[3],
				"win_condition": bl[4],
				"amount":bl[5]
			}
		bets.append(bd)


def main():

	window = build_layout()
	event_loop(window)
	window.close()



if __name__ == "__main__":
	main()