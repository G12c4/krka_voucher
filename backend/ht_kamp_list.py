import requests
import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict

# Define a data class for room data.
@dataclass
class GuestData:
    name: str
    dob: str

# Define the API URL.
API_URL = "http://frontdesk.dbtouch.com/integration/getReservationListOnDate?companyCode=PNqXkv9A&showBirthDates=true"

def get_rooms_kamp(room_list: List[str]) -> Dict[str, List[Dict[str, str]]]:

    # Try to request data from the API and handle potential errors.
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return {}
    except Exception as err:
        print(f'Error occurred: {err}')
        return {}

    data = response.json()
    kamp = data["data"][1]["reservationList"]

    kamp_guest_data = {}

    for room in kamp:
        guest_list = room["reservationGuestList"]
        # Check if the required data exists.
        if guest_list and room.get("unitName"):
            for guest in guest_list:
                name = guest.get("reservationGuestTitle")
                dob = guest.get("birthDate")
                # If name and dob are not empty, process them.
                if name and dob:
                    dob = datetime.datetime.strptime(dob, "%Y-%m-%d").strftime("%d/%m/%Y")
                    guest_data = GuestData(name=name, dob=dob)
                    # If room already in dict, append to it. Else, create a new list
                    if room["unitName"] in kamp_guest_data:
                        kamp_guest_data[room["unitName"]].append(asdict(guest_data))
                    else:
                        kamp_guest_data[room["unitName"]] = [asdict(guest_data)]

    # Return only the room data that matches the input room list.
    return {room: data for room, data in kamp_guest_data.items() if room in room_list}
            
def main():
    
    # Define the room list.
    room_list = ["01", "02"]
    rooms_data = get_rooms_kamp(room_list)
    print(rooms_data)

if __name__ == "__main__":
    main()
