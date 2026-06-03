from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import xml.etree.ElementTree as ET
import requests
from datetime import timedelta
from sqlalchemy.orm import Session
import re

from static import jwt_auth
from static.file_name import przygotuj_nazwe_pliku
from static.GUS_to_XML_ostateczny_converter import pobierz_gus_xml_lubelskie

from db.database import engine, Base, get_db, SessionLocal
from db.models import User, RaportZintegrowany


Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/style", StaticFiles(directory="style"), name="style")

GATUNKI_ANALITYCZNE = {
    "Wróbel domowy": "Passer domesticus",
    "Kaczka krzyżówka": "Anas platyrhynchos",
    "Gęś gęgawa": "Anser anser",
    "Gołąb miejski": "Columba livia",
    "Sikorka bogatka": "Parus major",
    "Wrona siwa": "Corvus cornix"
}

LATA_DO_ANALIZY = list(range(2014, 2025))


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = jwt_auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Nieprawidłowy login lub hasło")

    token = jwt_auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=jwt_auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/register")
async def register_user(
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Login musi mieć co najmniej 3 znaki.")

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise HTTPException(status_code=400, detail="Podaj poprawny adres e-mail.")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Hasło musi mieć co najmniej 6 znaków.")


    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Ten login lub e-mail jest już zajęty."
        )


    hashed_pwd = jwt_auth.get_password_hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_pwd)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Wystąpił błąd bazy danych.")


    token = jwt_auth.create_access_token(
        data={"sub": new_user.username},
        expires_delta=timedelta(minutes=jwt_auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": token, "token_type": "bearer", "message": "Konto zostało utworzone"}



@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})


@app.get("/")
def strona_glowna(request: Request):
    dane_do_wyslania = {
        "tytul": "Projekt Bioróżnorodność Lublina",
        "lata_badane": LATA_DO_ANALIZY,
        "czy_zalogowany": True
    }
    return templates.TemplateResponse(request=request, name="index.html", context=dane_do_wyslania)




@app.get("/api/ptaki/{rok}")
def pobierz_ptaki(rok: int, user=Depends(jwt_auth.get_current_user)):
    url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&year={rok}&limit=5"
    odpowiedz = requests.get(url)
    dane_json = odpowiedz.json()

    obserwacje = [
        {"gatunek": el.get("scientificName"), "miesiac": el.get("month")}
        for el in dane_json.get("results", [])
    ]

    return {
        "wiadomosc": f"Pobrano dane dla {rok}",
        "laczna_liczba_obserwacji_w_api": dane_json.get("count"),
        "przykladowe_ptaki": obserwacje
    }


@app.get("/api/eksport/xml/{gatunek}")
def eksportuj_wykres_xml(gatunek: str, user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    wyniki = db.query(RaportZintegrowany).filter(RaportZintegrowany.gatunek == gatunek).order_by(
        RaportZintegrowany.rok.asc()).all()

    root = ET.Element("AnalizaBioroznorodnosci")
    info = ET.SubElement(root, "Metadane")
    ET.SubElement(info, "Gatunek").text = gatunek
    ET.SubElement(info, "WygenerowanoPrzez").text = user.username

    dane_element = ET.SubElement(root, "DaneAnalityczne")

    for r in wyniki:
        rok_elem = ET.SubElement(dane_element, "RokPomiarowy", rok=str(r.rok))
        ET.SubElement(rok_elem, "LiczbaObserwacjiPtakow").text = str(r.liczba_ptakow_api)
        ET.SubElement(rok_elem, "Parki_ha").text = str(r.parki)
        ET.SubElement(rok_elem, "Zielence_ha").text = str(r.zielence)
        ET.SubElement(rok_elem, "ZielenUliczna_ha").text = str(r.zielen_uliczna)
        ET.SubElement(rok_elem, "ZielenOsiedlowa_ha").text = str(r.zielen_osiedlowa)
        ET.SubElement(rok_elem, "Cmentarze_ha").text = str(r.cmentarze)
        ET.SubElement(rok_elem, "LasyGminne_ha").text = str(r.lasy)

    xml_str = ET.tostring(root, encoding="utf-8", method="xml", xml_declaration=True)
    bezpieczna_nazwa = przygotuj_nazwe_pliku(gatunek, "xml")

    from fastapi.responses import Response
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{bezpieczna_nazwa}"'}
    )


@app.get("/api/eksport/json/{gatunek}")
def eksportuj_wykres_json(gatunek: str, user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    wyniki = db.query(RaportZintegrowany).filter(RaportZintegrowany.gatunek == gatunek).order_by(RaportZintegrowany.rok.asc()).all()

    dane_do_eksportu = {
        "metadane": {
            "gatunek": gatunek,
            "wygenerowano_przez": user.username
        },
        "dane_analityczne": [
            {
                "rok_pomiarowy": r.rok,
                "liczba_obserwacji": r.liczba_ptakow_api,
                "parki_ha": r.parki,
                "zielence_ha": r.zielence,
                "zielen_uliczna_ha": r.zielen_uliczna,
                "zielen_osiedlowa_ha": r.zielen_osiedlowa,
                "cmentarze_ha": r.cmentarze,
                "lasy_gminne_ha": r.lasy
            }
            for r in wyniki
        ]
    }

    bezpieczna_nazwa = przygotuj_nazwe_pliku(gatunek, "json")

    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=dane_do_eksportu,
        headers={"Content-Disposition": f'attachment; filename="{bezpieczna_nazwa}"'}
    )


@app.post("/api/integruj_i_zapisz")
def integruj_do_bazy(user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    try:
        # drzewo = ET.parse("zielen_lublin.xml")
        # korzen = drzewo.getroot()
        # korzen = pobierz_gus_xml_lubelskie()
        #
        # miasto = korzen.find("Miasto") if korzen.find("Miasto") is not None else korzen

        miasto = pobierz_gus_xml_lubelskie(LATA_DO_ANALIZY)

        zielen_slownik = {}
        for rok_elem in miasto.findall("Rok"):
            r_val = int(rok_elem.attrib.get("wartosc"))
            kategorie = {}
            for kat in rok_elem.findall("Kategoria"):
                kategorie[kat.attrib.get("nazwa")] = float(kat.text)
            zielen_slownik[r_val] = kategorie

        raporty_dodane_count = 0
        raporty_zaktualizowane_count = 0

        for rok in LATA_DO_ANALIZY:
            kategorie_roku = zielen_slownik.get(rok, {})

            for nazwa_pl, nazwa_latin in GATUNKI_ANALITYCZNE.items():
                istnieje = db.query(RaportZintegrowany).filter(
                    RaportZintegrowany.rok == rok,
                    RaportZintegrowany.gatunek == nazwa_pl
                ).first()

                if not istnieje:
                    # Pobieramy dane z API GBIF i tworzymy nowy wpis
                    url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&scientificName={nazwa_latin}&year={rok}&limit=1"
                    liczba_ptakow = requests.get(url).json().get("count", 0)

                    nowy_wpis = RaportZintegrowany(
                        rok=rok,
                        gatunek=nazwa_pl,
                        liczba_ptakow_api=liczba_ptakow,
                        parki=kategorie_roku.get("parki spacerowo - wypoczynkowe", 0.0),
                        zielence=kategorie_roku.get("zieleńce", 0.0),
                        zielen_uliczna=kategorie_roku.get("zieleń uliczna", 0.0),
                        zielen_osiedlowa=kategorie_roku.get("tereny zieleni osiedlowej", 0.0),
                        cmentarze=kategorie_roku.get("cmentarze", 0.0),
                        lasy=kategorie_roku.get("lasy gminne", 0.0)
                    )
                    db.add(nowy_wpis)
                    raporty_dodane_count += 1
                else:
                    # Aktualizujemy tylko dane o zieleni z pliku XML
                    istnieje.parki = kategorie_roku.get("parki spacerowo - wypoczynkowe", 0.0)
                    istnieje.zielence = kategorie_roku.get("zieleńce", 0.0)
                    istnieje.zielen_uliczna = kategorie_roku.get("zieleń uliczna", 0.0)
                    istnieje.zielen_osiedlowa = kategorie_roku.get("tereny zieleni osiedlowej", 0.0)
                    istnieje.cmentarze = kategorie_roku.get("cmentarze", 0.0)
                    istnieje.lasy = kategorie_roku.get("lasy gminne", 0.0)

                    raporty_zaktualizowane_count += 1

        db.commit()

        return {
            "status": "Sukces!",
            "wiadomosc": f"Zintegrowano dane. Dodano {raporty_dodane_count} nowych i zaktualizowano {raporty_zaktualizowane_count} istniejących rekordów."
        }
    except Exception as e:
        db.rollback()
        return {"status": "blad", "wiadomosc": str(e)}


@app.get("/api/wykres/{gatunek}")
def pobierz_dane_wykresu(gatunek: str, user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    wyniki = db.query(RaportZintegrowany).filter(RaportZintegrowany.gatunek == gatunek).order_by(RaportZintegrowany.rok.asc()).all()

    return {
        "lata": [r.rok for r in wyniki],
        "ptaki": [r.liczba_ptakow_api for r in wyniki],
        "parki": [r.parki for r in wyniki],
        "zielence": [r.zielence for r in wyniki],
        "zielen_uliczna": [r.zielen_uliczna for r in wyniki],
        "zielen_osiedlowa": [r.zielen_osiedlowa for r in wyniki],
        "cmentarze": [r.cmentarze for r in wyniki],
        "lasy": [r.lasy for r in wyniki]
    }
