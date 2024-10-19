from rao_credentials import username, password, rao_headers, rao_creds
from dataclasses import dataclass, field
from datetime import datetime
from requests import Session
import json

@dataclass
class VoucherCreator:
    # init
    date_in: str 
    grupe_odraslih: int = field(default_factory= 0)
    grupe_djece: int = field(default_factory= 0)
    grupa_djece_0_7: int = field(default_factory= 0)
    
    # class variables
    price_odrasli: dict = field(default_factory=dict, init=False)
    price_djeca: dict = field(default_factory=dict, init=False)
    price_djeca_0_7: dict = field(default_factory=dict, init=False)
    denominator: float = field(default_factory=int, init=False)
    voucher_numbers: list[str] = field(default_factory=list, init=False)
    voucher_ticket: str = field(default_factory=str, init=False)
    session: str = field(default_factory=str, init=False)
    
    def __post_init__(self):
        self._check_date_format()
        self._set_denominator()
        self._create_session()
        self._get_prices()
        self._get_voucher_numbers()

    def _set_denominator(self) -> None:
        mapping = {"1": None, "2": None, "3": None, "4": None, "5": None,
                    "6": 1.02, "7": 1.02, "8": 1.02, "9": 1.02, "10": 1.05,
                    "11": 1.05, "12": 1.05}

        date_format = "%d.%m.%Y"
        date_obj = datetime.strptime(self.date_in, date_format)
        month = date_obj.month
        self.denominator = mapping.get(str(month), "Not found")

    def _check_date_format(self) -> None:
        if "/" in self.date_in:
            self.date_in = self.date_in.replace("/", ".")

    def _create_session(self) -> None:
        s = Session()
        s.headers.update(rao_headers)
        response = s.post('https://apps.rao.hr/routing/login', data=json.dumps(rao_creds))
        if not response.ok:
            print(response.text)
        self.session = s

    def _get_prices(self) -> None:
        # Get articles request
        params = {
            'customer': '648458f2-df2e-4968-94c1-6e1d42103d5d',
            'date': self.date_in,
            'entrance': '0DA06AB2C0BB5038E0530AB1A8C0A516'
        }
        
        prices = self.session.post('https://apps.rao.hr/routing/getArticlesForDate', params=params, data=json.dumps(rao_creds))
        
        if prices.ok:
            self.price_odrasli = [{"price": x["price"], "maxd": x["maxDiscount"], "mind": x["minDiscount"], "margin": x["discountMargin"]} for x in prices.json() if x["name"] == "Grupe odraslih"][0]
            self.price_djeca = [{"price": x["price"], "maxd": x["maxDiscount"], "mind": x["minDiscount"], "margin": x["discountMargin"]} for x in prices.json() if x["name"] == "Grupe djece"][0]
            self.price_djeca_0_7 = [{"price": x["price"], "maxd": x["maxDiscount"], "mind": x["minDiscount"], "margin": x["discountMargin"]} for x in prices.json() if x["name"] == "Grupa djece 0-7"][0]
        else:
            print(f'Get prices Error: {prices.text}')
    
    def _get_voucher_numbers(self) -> None:
        response = self.session.post('https://apps.rao.hr/routing/getPartnerWebDocuments', data=json.dumps(rao_creds))
        if response.ok:
            eticket_json = response.json()
            self.voucher_numbers = [x['partnerWebID'] for x in eticket_json]
            if not self.voucher_numbers:
                print("Voucher numbers Error, no vouchers!")
        else:
            print(f'Get voucher numbers Error: {response.text}')
    
    def _get_new_voucher_number(self) -> None:
        old_voucher_numbers = set(self.voucher_numbers)
        self._get_voucher_numbers()
        new_voucher_numbers = set(self.voucher_numbers)
        result = list(new_voucher_numbers - old_voucher_numbers)
        result = result[0] if result else None
        if result:
            self.voucher_ticket = result
            print(f"New Voucher Ticket found!: {self.voucher_ticket}")
        else:
            print("Error no new voucher ticket found! Maybe new ticket wasn't created!")

    def create_ticket(self) -> None:
        # Create partner web document request
        data = {
            "locationIn": "F0F7B6F54D393ADFE0530AB1A8C0C87B",
            "locationOut": "F0F7B6F565073ADFE0530AB1A8C0C87B",
            "customer": "648458f2-df2e-4968-94c1-6e1d42103d5d",
            "amount": round(self.price_odrasli['price'] * self.grupe_odraslih / self.denominator, 1) + round(self.price_djeca['price'] * self.grupe_djece / self.denominator, 1),
            "note": None,
            "loginRequest": {
                "username": username,
                "password": password,
                "code": 202
            },
            "date": self.date_in,
            "articles": [
                {
                "oid":"F0CBBF6BD37C7E96E0530AB1A8C0EB6E",
                "name":"Grupe odraslih",
                "quantity":self.grupe_odraslih,
                "total":round(self.price_odrasli['price'] * self.grupe_odraslih / self.denominator, 1),
                "price":self.price_odrasli["price"],
                "margin":self.price_odrasli["margin"],
                "max":self.price_odrasli["maxd"],
                "min":self.price_odrasli["mind"]
            },
            {
                "oid":"F0CBBF6BD3827E96E0530AB1A8C0EB6E",
                "name":"Grupe djece",
                "quantity":self.grupe_djece,
                "total":round(self.price_djeca['price'] * self.grupe_djece / self.denominator, 1),
                "price":self.price_djeca["price"],
                "margin":self.price_djeca["margin"],
                "max":self.price_djeca["maxd"],
                "min":self.price_djeca["mind"]
            },
            {
                "oid":"F0CED43923B37097E0530AB1A8C01E5E",
                "name":"Grupa djece 0-7",
                "quantity":self.grupa_djece_0_7,
                "total":0,
                "price":self.price_djeca_0_7["price"],
                "margin":self.price_djeca_0_7["margin"],
                "max":self.price_djeca_0_7["maxd"],
                "min":self.price_djeca_0_7["mind"]}
            ],
            "services": [],
            "trips": []
        }
        response = self.session.post('https://apps.rao.hr/routing/createPartnerWebDocument', data=json.dumps(data))
        
        if not response.ok:
            print(f'Create ticket Error: {response.text}')
        
        self._get_new_voucher_number()

def main():
    # for testing
    date_in = "10.06.2023"
    grupe_odraslih = 1
    grupe_djece = 1
    grupa_djece_0_7 = 0
    
    ticket = VoucherCreator(date_in, grupe_odraslih, grupe_djece, grupa_djece_0_7)
    # ticket._get_new_voucher_number() ### only for testing
    ticket.create_ticket()
    # pass

if __name__ == '__main__':
    main()