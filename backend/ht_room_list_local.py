import json
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RoomDataProcessor:
    room_list: List[str]
    file_path: Union[Path, str] = Path(__file__).parent / "data.json"

    def filter_and_group_by_room(self, data: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Groups the given data by room number"""
        result = defaultdict(list)
        for person in data:
            if person["room"] in self.room_list:
                result[person["room"]].append({"name": person["name"], "dob": person["dob"]})
        return dict(result)

    def get_rooms(self) -> Union[Dict[str, List[Dict[str, str]]], bool]:
        """Returns the data for the specified rooms"""
        try:
            with open(self.file_path, "r") as f:
                res = json.load(f)
        except FileNotFoundError:
            logger.error(f"File {self.file_path} not found.")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.file_path}.")
            raise

        if not self.room_list:
            logger.error("Room list is empty.")
            return False

        room_data = self.filter_and_group_by_room(res)
        return room_data

def main():
    room_data_processor = RoomDataProcessor(room_list=["215", "111"])
    try:
        room_data = room_data_processor.get_rooms()
        print(room_data)
    except Exception as e:
        logger.error("Failed to get room data: %s", e)

if __name__ == "__main__":
    main()
