import json, random
from svdl import Location

def name_to_code(name: str) -> str:
    with open("./data/sorted.json", "r") as f:
        data: dict = json.load(f)
        for key in data:
            if data[key][0]["countryName"].lower() == name.lower():
                return key
    return None

def rand_country() -> str:
    with open("./data/sorted.json", "r") as f:
        data: dict = json.load(f)
        return data[random.choice(list(data.keys()))]

def rand_locs(*, amount: int) -> list[Location]:
    country = rand_country()
    locs = []
    while not len(locs) == amount:
        loc = country[random.randint(0, len(country) - 1)]
        if not loc in locs:
            locs.append(Location(loc))
    return locs

def get_all_countries() -> list[str]:
    with open("./data/sorted.json", "r") as f:
        return [key for key in json.load(f)]

def get_maps_link(loc: Location) -> str:
    return f"https://www.google.com/maps?q&layer=c&cbll={loc.latitude},{loc.longitude}&cbp=0,{loc.heading},0,0,{loc.pitch}"
