import PySimpleGUI as sg
from testAPI import *

td = {"auto_size_text" : False, "justification":"c"}
th = {"font":("Helvetica", 15, "underline")}
tb = {"font":("Helvetica", 12)}

# --------------------------------- Define Layout ---------------------------------
left_col = [[sg.Button('Callable Bets'), sg.Button('My Bets')],
			[sg.Listbox(values=[], enable_events=True, size=(40,20), key='-BET_LIST-')]
			]

right_col = [	[sg.Text('Bet Event', **td, **th )],
				[sg.Text('n/a', key="-BET_EVENT-", **td, **tb)],

				[sg.Text('Bet Value', **td,**th)],
				[sg.Text('n/a', key="-BET_VALUE-", **td, **tb)],

				[sg.Text('Bet Expiration', **td,**th)],
				[sg.Text('n/a', key="-BET_EXPIRATION-", **td, **tb)],

			  	[sg.Button("Accept Bet", key="-ACCEPT_BTN-")],
			  	[sg.Text("_" * 50)],

				[sg.Text('Make a bet', **td, **th)],
				[sg.Text("Bet Event:", justification="l"), sg.Input(key="-EVENT_INPUT-")],
				[sg.Text("Bet Amount:", justification="l"), sg.Input(key="-AMOUNT_INPUT-")],
				[sg.Text("Bet Expiration (mins):",justification="l"), sg.Input(key="-EXPIRATION_INPUT-")],
				[sg.Button("Send Bet", key="-SEND_BTN-")]
			]

# ----- Full layout -----
layout = [[sg.Column(left_col, element_justification='c'), sg.VSeperator(),sg.Column(right_col, element_justification='c')]]


# --------------------------------- Create Window ---------------------------------
window = sg.Window('Multiple Format Image Viewer', layout,resizable=True)



# ----- Run the Event Loop -----
# --------------------------------- Event Loop ---------------------------------
bet_dict = {}
selected_bet = None
is_on_callable = False

while True:
	event, values = window.read()
	if event in (sg.WIN_CLOSED, 'Exit'):
		break
	if event == sg.WIN_CLOSED or event == 'Exit':
		break

	
	if event == "Callable Bets":
		window["-ACCEPT_BTN-"].update(disabled = False)
		is_on_callable = True

		bet_dict = get_open_bets()
		open_best_list = [x["event"] for x in bet_dict]
		window['-BET_LIST-'].update(open_best_list)

	elif event == "My Bets":
		window["-ACCEPT_BTN-"].update(disabled = True)
		is_on_callable = False
		bet_dict = get_user_bets()
		pending_best_list = [x["event"] for x in bet_dict]
		window['-BET_LIST-'].update(pending_best_list)

	elif event == '-BET_LIST-':    # A bet was chosen from the bet box
		selected_bet = [x for x in bet_dict if x["event"] == values["-BET_LIST-"][0]][0]

		window["-BET_EVENT-"].update(selected_bet["event"])
		window["-BET_VALUE-"].update(selected_bet["amount"])
		window["-BET_EXPIRATION-"].update(selected_bet["expiration"])

	elif event == "-SEND_BTN-":
		window["-EVENT_INPUT-"].update("")
		window["-AMOUNT_INPUT-"].update("")
		window["-EXPIRATION_INPUT-"].update("")

	elif event == "-ACCEPT_BTN-":
		if selected_bet != None and is_on_callable:
			accept_bet(selected_bet["uuid"])
			bet_dict = get_open_bets()
			open_best_list = [x["event"] for x in bet_dict]
			window['-BET_LIST-'].update(open_best_list)




	print(event, values)
# --------------------------------- Close & Exit ---------------------------------
window.close()