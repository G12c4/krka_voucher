import json
from dataclasses import dataclass, asdict
from pathlib import Path
from time import sleep
from typing import List, Optional
from playwright.sync_api import sync_playwright
import db_engine
from creds import ht_username, ht_password
from pprint import pprint as print

@dataclass
class GuestData:
    room: str
    name: str
    dob: str

def navigate(page):
    """Navigate to the reservation list and set filters"""
    page.goto("https://frontdesk.hotelstouch.com/reservationGuest/list")
    page.click("text=")
    page.click("#startDateFilter")
    for _ in range(5):
        page.keyboard.press("ArrowLeft")
    page.keyboard.press("Enter")
    page.click("#endDateFilter")
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")
    page.click("text=Status")
    page.click("//label[@for='status_6']")
    page.click("text=Apply filters")
    sleep(3)

def fetch_guest_links(page) -> List[str]:
    try:
        num_of_pages = int(page.eval_on_selector("//input[@type='number']", "el => el.max"))
        all_guest_links = []
        for i in range(1, num_of_pages + 1):
            guest_links = page.eval_on_selector_all("//a[@title='Info']", "el => el.map(el => el.href)")
            all_guest_links.extend(guest_links)
            if i != num_of_pages:
                page.click("text=")
                sleep(2)
    except Exception as e:
        all_guest_links = page.eval_on_selector_all("//a[@title='Info']", "el => el.map(el => el.href)")

    return list(set(all_guest_links))

def fetch_guest_data(page, url: str) -> Optional[GuestData]:
    try:
        page.goto(url)
        room_number = page.eval_on_selector("//div[@class='infoHeaderTitle']", "el => el.innerText")[:3]
        html_content = page.content()

        start_index = html_content.index("var guestIdList = group") + 25
        end_index = len(html_content) - start_index - 150
        new_html_content = html_content[start_index:-end_index]

        start = ': ['
        end = '];'
        guest_id = new_html_content.split(start)[1].split(end)[0].split(", ")

        guest_data = []
        for g_url in guest_id:
            page.goto(f"https://frontdesk.hotelstouch.com/guest/ajaxModalForm?reservationGuestId={g_url}")
            guest_first_name = page.eval_on_selector("#firstName", "el => el.value")
            guest_last_name = page.eval_on_selector("#lastName", "el => el.value")
            guest_full_name = f"{guest_first_name} {guest_last_name}"
            guest_dob = page.eval_on_selector("//input[@id='birthDate']", "el => el.value")

            guest_data.append(GuestData(room=room_number, name=guest_full_name, dob=guest_dob))

        return guest_data
    except Exception as e:
        print(f"Error when fetching guest data for {url}: {e}")
        return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://management.hotelstouch.com/login/auth")
        page.fill("[placeholder=\"Email\"]", ht_username)
        page.fill("[placeholder=\"Password\"]", ht_password)
        page.click("button:has-text(\"Login\")")

        navigate(page)
        guest_links = fetch_guest_links(page)
        # print(guest_links)
        
        guest_data = []
        for url in guest_links:
            data = fetch_guest_data(page, url)
            if data is not None:
                guest_data.extend(data)  # Use extend instead of append as fetch_guest_data returns a list

        guest_data.sort(key=lambda data: data.room)

        # print(guest_data)

        browser.close()

        json_data = json.dumps([data.__dict__ for data in guest_data], indent=4)
        db_data = [asdict(gd) for gd in guest_data]
        db_engine.delete_and_repopulate_data(guest_data=(db_data))
        Path('data.json').write_text(json_data)

if __name__ == "__main__":
    main()