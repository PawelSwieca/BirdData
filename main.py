from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import xml.etree.ElementTree as ET
import requests

from datetime import timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import create_engine, Column, Integer, Float
from sqlalchemy.orm import declarative_base, sessionmaker

import jwt_auth

SQLALCHEMY_DATABASE_URL = "sqlite:///./baza_projektowa.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    isolation_level="SERIALIZABLE"
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class RaportZintegrowany(Base):
    __tablename__ = "raporty_zintegrowane"
    id = Column(Integer, primary_key=True, index=True)
    rok = Column(Integer, unique=True, index=True)
    powierzchnia_parkow_ha = Column(Float)
    liczba_ptakow_api = Column(Integer)


Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/style", StaticFiles(directory="style"), name="style")


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = jwt_auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Nieprawidłowy login lub hasło")

    token = jwt_auth.create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=jwt_auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/")
def strona_glowna(request: Request):
    dane_do_wyslania = {
        "tytul": "Projekt Bioróżnorodność Lublina",
        "lata_badane": [2018, 2019, 2020, 2021, 2022],
        "czy_zalogowany": True
    }
    return templates.TemplateResponse(request=request, name="index.html", context=dane_do_wyslania)



@app.get("/api/ptaki/{rok}")
def pobierz_ptaki(rok: int, user=Depends(jwt_auth.get_current_user)):
    url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&year={rok}&limit=5"
    odpowiedz = requests.get(url)
    dane_json = odpowiedz.json()
    obserwacje = [{"gatunek": el.get("scientificName"), "miesiac": el.get("month")} for el in
                  dane_json.get("results", [])]
    return {"wiadomosc": f"Pobrano dane dla {rok}", "laczna_liczba_obserwacji_w_api": dane_json.get("count"),
            "przykladowe_ptaki": obserwacje}


@app.get("/api/ptaki/{rok}/{gatunek}")
def pobierz_ptaki_gatunek(rok: int, gatunek: str, user=Depends(jwt_auth.get_current_user)):
    url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&scientificName={gatunek}&year={rok}&limit=5"
    odpowiedz = requests.get(url)
    dane_json = odpowiedz.json()
    obserwacje = [{"gatunek": el.get("scientificName"), "miesiac": el.get("month")} for el in
                  dane_json.get("results", [])]
    return {"wiadomosc": f"Pobrano dane dla {rok} dla gatunku {gatunek}",
            "laczna_liczba_obserwacji_w_api": dane_json.get("count"), "przykladowe_ptaki": obserwacje}


@app.get("/api/zielen")
def odczytaj_xml(user=Depends(jwt_auth.get_current_user)):
    try:
        drzewo = ET.parse("zielen_lublin.xml")
        korzen = drzewo.getroot()
        wyniki = []
        for rok_elem in korzen.find("Miasto").findall("Rok"):
            rok_wartosc = int(rok_elem.attrib.get("wartosc"))
            for kat in rok_elem.findall("Kategoria"):
                if kat.attrib.get("nazwa") == "parki spacerowo - wypoczynkowe":
                    wyniki.append({"rok": rok_wartosc, "powierzchnia_parkow_ha": float(kat.text)})
        return {"statystyki": wyniki}
    except FileNotFoundError:
        return {"blad": "Brak pliku zielen_lublin.xml"}


@app.post("/api/integruj_i_zapisz")
def integruj_do_bazy(user=Depends(jwt_auth.get_current_user)):
    db = SessionLocal()
    try:
        dane_xml = odczytaj_xml(user)
        if "blad" in dane_xml:
            return dane_xml

        raporty_dodane = []
        for stat in dane_xml["statystyki"]:
            rok = stat["rok"]
            powierzchnia = stat["powierzchnia_parkow_ha"]

            url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&year={rok}&limit=1"
            liczba_ptakow = requests.get(url).json().get("count", 0)

            istniejacy_raport = db.query(RaportZintegrowany).filter(RaportZintegrowany.rok == rok).first()
            if not istniejacy_raport:
                nowy_wpis = RaportZintegrowany(rok=rok, powierzchnia_parkow_ha=powierzchnia,
                                               liczba_ptakow_api=liczba_ptakow)
                db.add(nowy_wpis)
                raporty_dodane.append(rok)

        db.commit()
        return {"status": "Sukces!", "dodane_lata": raporty_dodane}
    except Exception as e:
        db.rollback()
        return {"status": "blad", "wiadomosc": str(e)}
    finally:
        db.close()