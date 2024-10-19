from typing import List, Dict
from datetime import date

def calc_dates(list_of_dates: List[str]) -> Dict[str, int]:
    current_year = date.today().year

    age_groups = []
    
    for birth_date in list_of_dates:
        try:
            birth_year = int(birth_date[-4:])
        except ValueError:
            raise ValueError(f"Could not convert '{birth_date[-4:]}' to an integer.")

        if current_year - birth_year < 7:
            age_groups.append("Grupa djece 0-7")
        elif current_year - birth_year < 18:
            age_groups.append("Grupe djece")
        else:
            age_groups.append("Grupe odraslih")

    group_counts = {
        "Grupe odraslih": age_groups.count("Grupe odraslih"),
        "Grupe djece": age_groups.count("Grupe djece"),
        "Grupa djece 0-7": age_groups.count("Grupa djece 0-7")
    }

    return group_counts

def main():
    gr_in = ["22.06.1986", "22.06.2013", "22.06.2022"]
    dates = calc_dates(gr_in)
    odrasli = dates["Grupe odraslih"]
    djeca = dates["Grupe djece"]
    djeca0_7 = dates["Grupa djece 0-7"]
    print(odrasli)
    print(djeca)
    print(djeca0_7)

if __name__ == '__main__':
    main()