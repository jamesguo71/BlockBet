import PySimpleGUI as sg
from testAPI import *



# --------------------------------- Define Layout ---------------------------------


left_col = [[sg.Button('Open Bets'), sg.Button('Pending Bets'), sg.Button('My Bets')],
			[sg.Listbox(values=[], enable_events=True, size=(40,20), key='-BET_LIST-')]
			]

right_col = [	[sg.Text('Bet Event', key="-BET_EVENT-")],
				[sg.Text('Bet Value', key="-BET_VALUE-"), sg.Text('Bet Expiration', key="-BET_EXPIRATION-")],
			  	[sg.Button("Accept")],
			  	[sg.Text("_" * 30)],
				[sg.Text('Make a bet')],
			]

# ----- Full layout -----
layout = [[sg.Column(left_col, element_justification='c'), sg.VSeperator(),sg.Column(right_col, element_justification='c')]]


# --------------------------------- Create Window ---------------------------------
window = sg.Window('Multiple Format Image Viewer', layout,resizable=True)



# ----- Run the Event Loop -----
# --------------------------------- Event Loop ---------------------------------
bet_dict = {}
while True:
	event, values = window.read()
	if event in (sg.WIN_CLOSED, 'Exit'):
		break
	if event == sg.WIN_CLOSED or event == 'Exit':
		break

	
	if event == "Open Bets":
		bet_dict = get_open_bets()
		open_best_list = [x["event"] for x in bet_dict]
		window['-BET_LIST-'].update(open_best_list)

	elif event == "Pending Bets":
		bet_dict = get_pending_bets()
		pending_best_list = [x["event"] for x in bet_dict]
		window['-BET_LIST-'].update(pending_best_list)

	elif event == '-BET_LIST-':    # A bet was chosen from the bet box
		bet = [x for x in bet_dict if x["event"] == values["-BET_LIST-"][0]][0]
		
		window["-BET_EVENT-"].update(bet["event"])
		window["-BET_VALUE-"].update(bet["amount"])
		window["-BET_EXPIRATION-"].update(bet["expiration"])

	print(event, values)
# --------------------------------- Close & Exit ---------------------------------
window.close()