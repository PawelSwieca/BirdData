from fastapi import FastAPI
import xml.etree.ElementTree as ET

import requests
from requests import Request

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
app = FastAPI()


templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/style", StaticFiles(directory="style"), name="style")


@app.get("/")
def strona_glowna(request: Request):
    # Zmienne, które wysyłamy na templates
    dane_do_wyslania = {
        "tytul": "Projekt Bioróżnorodność Lublina",
        "lata_badane": [2018, 2019, 2020, 2021, 2022],
        "czy_zalogowany": True
    }
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, **dane_do_wyslania})


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# ---------------------------------------------------------
# 1. ENDPOINT: Pobieranie ptaków z REST API (GBIF)
# ---------------------------------------------------------
@app.get("/api/ptaki/{rok}")
def pobierz_ptaki(rok: int):

    url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&year={rok}&limit=5"

    odpowiedz = requests.get(url)
    dane_json = odpowiedz.json()

    obserwacje = []
    for element in dane_json.get("results", []):
        obserwacje.append({
            "gatunek": element.get("scientificName"),
            "miesiac": element.get("month"),
            "rok": element.get("year")
        })

    return {
        "wiadomosc": f"Pobrano dane o ptakach dla roku {rok}",
        "laczna_liczba_obserwacji_w_api": dane_json.get("count"),
        "przykladowe_ptaki": obserwacje
    }


# ---------------------------------------------------------
# 2. ENDPOINT: Odczyt z pliku XML
# ---------------------------------------------------------
@app.get("/api/zielen")
def odczytaj_xml():

    try:
        drzewo = ET.parse("zielen_lublin.xml")
        korzen = drzewo.getroot()

        wyniki = []
        miasto = korzen.find("Miasto")
        nazwa_miasta = miasto.attrib.get("nazwa")

        # Przechodzimy przez każdy rok w XML
        for rok_elem in miasto.findall("Rok"):
            rok_wartosc = rok_elem.attrib.get("wartosc")

            # Szukamy tylko parków
            for kat in rok_elem.findall("Kategoria"):
                if kat.attrib.get("nazwa") == "parki spacerowo - wypoczynkowe":
                    wyniki.append({
                        "rok": rok_wartosc,
                        "powierzchnia_parkow_ha": float(kat.text)
                    })

        return {"miasto": nazwa_miasta, "statystyki": wyniki}

    except FileNotFoundError:
        return {"blad": "Nie znaleziono pliku zielen_lublin.xml!"}
