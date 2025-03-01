from playwright.async_api import async_playwright
from dataclasses import dataclass, field
import logging
from rich.logging import RichHandler
from requests import Session
from datetime import datetime
from rich import print
import asyncio
import creds
import json

# Configure the file handler
file_handler = logging.FileHandler("logfile.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

FORMAT = "%(message)s"
logging.basicConfig(
    level="DEBUG", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(), file_handler]
)

log = logging.getLogger("rich")
log.addHandler(file_handler)


@dataclass
class VoucherCreator:
    # init
    date_in: str
    ulaz_in: str
    grupe_odraslih: int = None
    grupe_djece: int = None
    grupa_djece_0_7: int = None
    headless: bool = True

    # class variables
    voucher_numbers: list[str] = field(default_factory=list, init=False)
    voucher_ticket: str = field(default_factory=str, init=False)
    time_slots: dict = field(default_factory=dict, init=False)
    session: str = field(default_factory=str, init=False)

    def __post_init__(self):
        self._check_date_format()
        self._create_session()
        self._get_voucher_numbers()
        self._get_time_slots()

    def _check_date_format(self) -> None:
        if "/" in self.date_in:
            self.date_in = self.date_in.replace("/", ".")

    def _create_session(self) -> None:
        s = Session()
        s.headers.update(creds.rao_headers)
        response = s.post(
            "https://apps.rao.hr/routing/login", data=json.dumps(creds.rao_creds)
        )
        if not response.ok:
            print(response.text)
        self.session = s

    def _get_voucher_numbers(self) -> None:
        response = self.session.post(
            "https://apps.rao.hr/routing/getPartnerWebDocuments",
            data=json.dumps(creds.rao_creds),
        )
        if response.ok:
            eticket_json = response.json()
            self.voucher_numbers = [x["partnerWebID"] for x in eticket_json]
            log.info(f"Found {len(self.voucher_numbers)} old vouchers")
            if not self.voucher_numbers:
                log.error("Voucher numbers Error, no vouchers!")
        else:
            log.error(f"Get voucher numbers Error: {response.text}")

    def _get_new_voucher_number(self) -> None:
        old_voucher_numbers = set(self.voucher_numbers)
        self._get_voucher_numbers()
        new_voucher_numbers = set(self.voucher_numbers)
        result = list(new_voucher_numbers - old_voucher_numbers)
        result = result[0] if result else None
        if result:
            self.voucher_ticket = result
            log.info(f"New voucher created: {self.voucher_ticket}")
        else:
            log.error(
                "Error no new voucher ticket found! Maybe new ticket wasn't created!"
            )

    def _get_time_slots(self) -> None:
        # get start time for entrance
        krka_url = f"https://apps.rao.hr/routing/getLocationsForKrka?additional={self.date_in}X.XPjesaciX.X0DA06AB2C0BB5038E0530AB1A8C0A516"
        response = self.session.post(krka_url, data=json.dumps(creds.rao_creds))
        response = response.json()
        if response:
            self.time_slots = {
                "Ulaz": response[0].get("from").split(' ')[1],
                "Izlaz": response[1].get("from").split(' ')[1],
            }
            if not self.time_slots:
                log.info("Time slots Error, no time slots!")
        else:
            log.info(f"Get Time slots Error: {response.text}")

    def _get_day(self, string):
        # Returns the day from the given string.
        date = datetime.strptime(string, "%d.%m.%Y")
        return date.month - 1

    #deprecated
    def _get_entry_exit_periods(self, month):
        periods = {
            'January': ('08:00', '09:00'),
            'February': ('09:00', '10:00'),
            'March': ('09:00', '10:00'),
            'April': ('08:00', '09:00'),
            'May': ('08:00', '09:00'),
            'June': ('08:00', '09:00'),
            'July': ('08:00', '09:00'),
            'August': ('08:00', '09:00'),
            'September': ('08:00', '09:00'),
            'October': ('09:00', '10:00'),
            'November': ('09:00', '10:00'),
            'December': ('09:00', '10:00')
        }
        return periods.get(month, (None, None))

    #deprecated
    def _get_times_for_date(self, date_in):
        # Parse the date string to extract the month
        day, month, year = map(int, date_in.split('.'))

        # Convert month number to month name
        month_name = datetime(year, month, day).strftime('%B')

        # Get entry and exit times
        entry_time, exit_time = self._get_entry_exit_periods(month_name)

        return entry_time, exit_time

    async def _login(self) -> None:
        """Perform login operation."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()

        # Add logging to verify browser and context initialized
        log.info("Browser launched")
        log.info("New context created")

        self.page = await self.context.new_page()
        try:
            await self.page.goto("http://oa.rao.hr:8050/#/eticket/partner-web")
            await self.page.fill('input[type="text"]', creds.username)
            await self.page.fill('input[type="password"]', creds.password)
            await self.page.click("text=Prijava")
            async with self.page.expect_navigation(
                timeout=60000
            ):  # increase timeout to 60 seconds
                await self.page.click('img[alt="NP KRKA"]')
            await self.page.goto(
                "http://oa.rao.hr:8050/#/eticket/partner-web/nova-najava-krka"
            )
        except Exception as e:
            log.error(f"Error logging in: {e}", exc_info=True)
            await self._close()
            raise

    async def _create_ticket(self):
        """Method to handle ticket actions."""
        log.info("Login successful!")
        try:
            await self.page.get_by_text("Odaberite klijenta").click()
            await self.page.get_by_text("VRATA KRKE D.O.O.", exact=True).click()
            await self.page.get_by_text("Datum dolaska").click()
            await self.page.get_by_title("Odaberite mjesec").select_option(
                f"{self._get_day(self.date_in)}"
            )
            await self.page.get_by_label(f"{self.date_in}").click()
            await self.page.get_by_text("Odaberite ulaz", exact=True).click()
            await self.page.get_by_text(f"{self.ulaz_in}").first.click()
            await self.page.get_by_text("Odaberite nacin ulaska u park").click()
            await self.page.get_by_text("Pjesaci").first.click()
            await self.page.get_by_text("Odaberite izlaz").click()
            await self.page.get_by_text(f"{self.ulaz_in}").nth(2).click()
            await self.page.get_by_text("Odaberite nacin izlaska iz parka").click()
            await self.page.get_by_text("Pjesaci").nth(2).click()
            await self.page.get_by_text("Dohvati periode ulaska").click()
            entry_time, exit_time = self.time_slots.get("Ulaz"), self.time_slots.get("Izlaz")
            await self.page.get_by_role("cell", name=f"{self.date_in} {entry_time}").click()
            await self.page.get_by_role("dialog", name="Odaberite ulaznicu").click()
            await self.page.get_by_role("cell", name=f"{self.date_in} {exit_time}").click()
            if self.grupe_odraslih:
                await self.page.get_by_role("button", name=" Dodaj ulaznicu").click()
                await self.page.get_by_role("cell", name="Grupe odraslih", exact=True).click()
                await self.page.get_by_label("Količina").fill(f"{self.grupe_odraslih}")
                await self.page.get_by_role("button", name="Dodaj u košaricu").click()
            if self.grupe_djece:
                await self.page.get_by_role("button", name=" Dodaj ulaznicu").click()
                await self.page.get_by_role("cell", name="Grupe djece", exact=True).click()
                await self.page.get_by_label("Količina").fill(f"{self.grupe_djece}")
                await self.page.get_by_role("button", name="Dodaj u košaricu").click()
            if self.grupa_djece_0_7:
                await self.page.get_by_role("button", name=" Dodaj ulaznicu").click()
                await self.page.get_by_role("cell", name="Grupa djece 0-7", exact=True).click()
                await self.page.get_by_label("Količina").fill(f"{self.grupa_djece_0_7}")
                await self.page.get_by_role("button", name="Dodaj u košaricu").click()
            log.info("Ticked data entered successful!")
            await asyncio.sleep(3)
        except Exception as e:
            log.error(f"Error handling ticket: {e}", exc_info=True)
            await self._close()
            raise

    async def _submit_form(self):
        """Method to submit the form."""
        try:
            await self.page.click("button[class='btn btn-primary fa fa-check']")
            # await self.page.get_by_role("button", name=" Kreiraj najavu").click()
            await asyncio.sleep(2)
            log.info("New ticket successfully created!")
            self._get_new_voucher_number()
        except Exception as e:
            log.error(f"Error submitting form: {e}", exc_info=True)
            await self._close()
            raise

    async def _close(self) -> None:
        """Close context and browser."""
        try:
            if self.context:
                await self.context.close()
        except Exception as e:
            log.error(f"Error closing context: {e}", exc_info=True)
        finally:
            if self.browser:
                await self.browser.close()

    async def run(self) -> None:
        try:
            await self._login()
            await self._create_ticket()
            await self._submit_form()
        except asyncio.CancelledError:
            log.error("Task was cancelled", exc_info=True)
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
        finally:
            await self._close()

    async def run_test(self) -> None:
        try:
            await self._login()
            await self._create_ticket()
        except asyncio.CancelledError:
            log.error("Task was cancelled", exc_info=True)
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
        finally:
            await self._close()


async def main():
    # for testing
    date_in = "02.03.2025"
    grupe_odraslih = 1
    grupe_djece = 1
    grupa_djece_0_7 = 1

    ticket = VoucherCreator(
        date_in=date_in,
        grupe_odraslih=grupe_odraslih,
        grupe_djece=grupe_djece,
        grupa_djece_0_7=grupa_djece_0_7,
        ulaz_in="LOZOVAC",
        headless=False,
    )

    await ticket.run_test()

    ticket_num = ticket.voucher_ticket
    if not ticket_num:
        log.error("New voucher number not found")
    else:
        log.info(f"New voucher number: {ticket_num}")


if __name__ == "__main__":
    asyncio.run(main())