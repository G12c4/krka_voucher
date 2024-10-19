from write_data_excel import write_data_to_excel
# import ht_room_list_local as rooms
import ht_kamp_list as kamp
import calc_dates as cd
from create_ticket_pw import VoucherCreator
import db_engine
from datetime import date, timedelta
import PySimpleGUI as sg
from dataclasses import dataclass
import asyncio
import csv


@dataclass
class GUIConfig:
    """Dataclass to store various GUI settings"""

    font_size: int = 90
    name_box_size: tuple = (20, 1)
    gr_box_size: tuple = (10, 1)
    output_box_size: tuple = (60, 4)


# This function generates a list of room numbers.
def get_room_list():
    return [
        "101",
        "102",
        "103",
        "104",
        "105",
        "106",
        "107",
        "108",
        "109",
        "110",
        "111",
        "112",
        "115",
        "116",
        "117",
        "118",
        "119",
        "120",
        "121",
        "122",
        "123",
        "124",
        "125",
        "126",
        "127",
        "128",
        "129",
        "130",
        "201",
        "203",
        "204",
        "206",
        "207",
        "208",
        "209",
        "210",
        "211",
        "212",
        "215",
        "216",
        "217",
        "218",
        "219",
        "220",
        "221",
        "224",
        "225",
        "226",
        "227",
        "228",
        "229",
    ]


# This function generates a list of dates.
def get_date_list():
    return [
        str((date.today() + timedelta(x + 1)).strftime("%d.%m.%Y"))
        for x in range(-1, 8)
    ]


# This function creates the layout of the GUI.
def create_layout(config):
    sobe_drop = get_room_list()
    dates_drop = get_date_list()
    employee_name = []
    with open(r"C:\Vouchers\krka_voucer\backend\employees.csv", 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            for i in row:
                employee_name.append(i.strip())

    # Simplified layout using loops for repetitious elements
    person_rows = [
        [
            sg.Text(f"#{i+1}", font=config.font_size),
            sg.Text("Ime i Prezime:", font=config.font_size),
            sg.Input(
                key=f"ime{i+1}",
                size=config.name_box_size,
                background_color="white",
                font=config.font_size,
            ),
            sg.Text("Datum rođenja:", font=config.font_size),
            sg.Input(
                key=f"gr{i+1}",
                size=config.gr_box_size,
                background_color="white",
                font=config.font_size,
            ),
        ]
        for i in range(9)
    ]

    layout = [
        [
            sg.Text("Zaposlenik:", font=config.font_size),
            sg.Combo(
                employee_name,
                key="-zaposlenik-",
                size=(10, 1),
                background_color="white",
                font=config.font_size,
            ),
        ],
        [
            sg.Text("Datum boravka:", font=config.font_size),
            sg.Combo(
                dates_drop,
                key="-datum-",
                size=(10, 1),
                background_color="white",
                font=config.font_size,
            ),
        ],
        [sg.Text("Ulaz: Lozovac", font=config.font_size)],
        [
            sg.Text("Soba/e:", font=config.font_size),
            sg.Combo(
                sobe_drop,
                key="-sobe1-",
                size=(10, 1),
                background_color="white",
                font=config.font_size,
            ),
            sg.Combo(
                sobe_drop,
                key="-sobe2-",
                size=(10, 1),
                background_color="white",
                font=config.font_size,
            ),
            sg.Combo(
                sobe_drop,
                key="-sobe3-",
                size=(10, 1),
                background_color="white",
                font=config.font_size,
            ),
            sg.Button("Učitaj", font=config.font_size),
        ],
        *person_rows,
        [
            sg.Text(
                key="-OUT-",
                size=config.output_box_size,
                relief="sunken",
                background_color="white",
                text_color="black",
                font=config.font_size,
            )
        ],
        [
            sg.Button("Najava & Ispis", font=config.font_size),
            sg.Button("Poništi", font=config.font_size),
        ],
    ]

    return layout


# This function handles GUI events.
def handle_events(window):
    sobe_drop = get_room_list()

    # create event loop
    while True:
        event, values = window.read()
        # end program if user closes window or presses Izlaz button
        if event == sg.WINDOW_CLOSED:
            break
        if event == "Učitaj":
            sobe_in = [values["-sobe1-"], values["-sobe2-"], values["-sobe3-"]]
            if any(x in sobe_drop for x in sobe_in):
                getrooms = db_engine.get_guests_from_rooms(rooms=sobe_in)

                # clear all windows
                for win in range(1, 10):
                    window[f"ime{win}"].update("")
                    window[f"gr{win}"].update("")
                window[f"gr{win}"].update("")

                # update names and dates for found rooms
                counter = 1
                for room, occupants in getrooms.items():
                    for occupant in occupants:
                        window[f"ime{counter}"].update(occupant["name"])
                        window[f"gr{counter}"].update(occupant["dob"])
                        counter += 1

            else:
                getrooms = kamp.get_rooms_kamp(sobe_in)
                for win in range(1, 10):
                    window[f"ime{win}"].update("")
                    window[f"gr{win}"].update("")
                for x, name in enumerate(getrooms[0], 1):
                    window[f"ime{x}"].update(name)
                    for y, dob in enumerate(getrooms[1], 1):
                        window[f"gr{y}"].update(dob)

        if event == "Najava & Ispis":
            datum_in = values["-datum-"]
            zaposlenik = values["-zaposlenik-"]
            ime_in = [
                values["ime1"],
                values["ime2"],
                values["ime3"],
                values["ime4"],
                values["ime5"],
                values["ime6"],
                values["ime7"],
                values["ime8"],
                values["ime9"],
            ]
            ime_in = [x for x in ime_in if x != ""]
            gr_in = [
                values["gr1"],
                values["gr2"],
                values["gr3"],
                values["gr4"],
                values["gr5"],
                values["gr6"],
                values["gr7"],
                values["gr8"],
                values["gr9"],
            ]
            gr_in = [x for x in gr_in if x != ""]
            if datum_in and zaposlenik:
                grupe_odraslih = cd.calc_dates(gr_in)["Grupe odraslih"]
                grupe_djece = cd.calc_dates(gr_in)["Grupe djece"]
                grupa_djece_0_7 = cd.calc_dates(gr_in)["Grupa djece 0-7"]
                if (
                    datum_in
                    and grupe_odraslih >= 0
                    and grupe_djece >= 0
                    and grupa_djece_0_7 >= 0
                ):
                    ticket = VoucherCreator(
                        date_in=datum_in,
                        grupe_odraslih=grupe_odraslih,
                        grupe_djece=grupe_djece,
                        grupa_djece_0_7=grupa_djece_0_7,
                        ulaz_in="LOZOVAC",
                        headless=True,
                    )
                    asyncio.run(ticket.run())
                    # asyncio.run(ticket.run_test())  # for testing
                    ticket_number = ticket.voucher_ticket
                    # ticket_number = ["1234test"]  # for testing
                else:
                    print(
                        "Data missing from: datum_in, grupe_odraslih, grupe_djece, grupa_djece_0_7"
                    )
                    print(datum_in, grupe_odraslih, grupe_djece, grupa_djece_0_7)
                if ticket_number:
                    print(f"Ticket number: {ticket_number}")
                    write_data_to_excel(
                        ticket_number, datum_in, "LOZOVAC", "LOZOVAC", ime_in, gr_in
                    )
                    db_engine.add_tickets_sold(zaposlenik)
                    # print("Printing ticket")  # for testing
                    print("Print successful!")
                    window["-OUT-"].update("Najava...")
                else:
                    print("Error no new ticket number")
                    window["-OUT-"].update("***GREŠKA*** Broj vouchera nedostupan!")
                    window["-OUT-"].update("Najava...")
                    window["-OUT-"].update("Ispis...")
            else:
                window["-OUT-"].update("***GREŠKA*** Nedostaje polje!")

        if event == "Poništi":
            for win in range(1, 10):
                window[f"ime{win}"].update("")
                window[f"gr{win}"].update("")
            window["-sobe1-"].update("")
            window["-sobe2-"].update("")
            window["-sobe3-"].update("")
            # window["-datum-"].update("")
            window["-OUT-"].update("")
            # window["-ulaz-"].update("")
            # window["-izlaz-"].update("")


# This function runs the GUI.
def run_gui():
    config = GUIConfig()
    layout = create_layout(config)

    # create window
    window = sg.Window("Najava Voucher", layout, size=(600, 500), resizable=False)

    handle_events(window)

    window.close()


run_gui()
