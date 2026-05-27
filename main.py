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
    "Gęś gęgawa": "Anser anser"
}




@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = jwt_auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Nieprawidłowy login lub hasło")

    token = jwt_auth.create_access_token(
        data={"sub": user.username},  # user is now a SQLAlchemy object, so use .username instead of ["username"]
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
        "lata_badane": [2018, 2019, 2020, 2021, 2022],
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
    # 1. Pobieramy dane z bazy tak samo jak do wykresu
    wyniki = db.query(RaportZintegrowany).filter(RaportZintegrowany.gatunek == gatunek).order_by(
        RaportZintegrowany.rok.asc()
    ).all()


    root = ET.Element("AnalizaBioroznorodnosci")
    info = ET.SubElement(root, "Metadane")
    ET.SubElement(info, "Gatunek").text = gatunek
    ET.SubElement(info, "WygenerowanoPrzez").text = user.username

    dane_element = ET.SubElement(root, "DaneAnalityczne")

    for r in wyniki:
        rok_elem = ET.SubElement(dane_element, "RokPomiarowy", rok=str(r.rok))
        ET.SubElement(rok_elem, "PowierzchniaParkow_ha").text = str(r.powierzchnia_parkow_ha)
        ET.SubElement(rok_elem, "LiczbaObserwacji").text = str(r.liczba_ptakow_api)


    xml_str = ET.tostring(root, encoding="utf-8", method="xml", xml_declaration=True)


    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="raport_{gatunek.replace(" ", "_")}.xml"'
        }
    )


@app.get("/api/eksport/json/{gatunek}")
def eksportuj_wykres_json(gatunek: str, user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    wyniki = db.query(RaportZintegrowany).filter(RaportZintegrowany.gatunek == gatunek).order_by(
        RaportZintegrowany.rok.asc()
    ).all()

    dane_do_eksportu = {
        "metadane": {
            "gatunek": gatunek,
            "wygenerowano_przez": user.username
        },
        "dane_analityczne": [
            {
                "rok_pomiarowy": r.rok,
                "powierzchnia_parkow_ha": r.powierzchnia_parkow_ha,
                "liczba_obserwacji": r.liczba_ptakow_api
            }
            for r in wyniki
        ]
    }


    return JSONResponse(
        content=dane_do_eksportu,
        headers={
            "Content-Disposition": f'attachment; filename="raport_{gatunek.replace(" ", "_")}.json"'
        }
    )

@app.post("/api/integruj_i_zapisz")
def integruj_do_bazy(user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    try:
        drzewo = ET.parse("zielen_lublin.xml")
        korzen = drzewo.getroot()

        miasto = korzen.find("Miasto")
        if miasto is None:
            miasto = korzen

        zielen_slownik = {}
        for rok_elem in miasto.findall("Rok"):
            r_val = int(rok_elem.attrib.get("wartosc"))
            for kat in rok_elem.findall("Kategoria"):
                if kat.attrib.get("nazwa") == "parki spacerowo - wypoczynkowe":
                    zielen_slownik[r_val] = float(kat.text)

        raporty_dodane_count = 0

        for rok in [2018, 2019, 2020, 2021, 2022]:
            powierzchnia = zielen_slownik.get(rok, 0.0)

            for nazwa_pl, nazwa_latin in GATUNKI_ANALITYCZNE.items():
                istnieje = db.query(RaportZintegrowany).filter(
                    RaportZintegrowany.rok == rok,
                    RaportZintegrowany.gatunek == nazwa_pl
                ).first()

                if not istnieje:
                    url = f"https://api.gbif.org/v1/occurrence/search?country=PL&stateProvince=Lubelskie&classKey=212&scientificName={nazwa_latin}&year={rok}&limit=1"
                    liczba_ptakow = requests.get(url).json().get("count", 0)

                    nowy_wpis = RaportZintegrowany(
                        rok=rok,
                        gatunek=nazwa_pl,
                        powierzchnia_parkow_ha=powierzchnia,
                        liczba_ptakow_api=liczba_ptakow
                    )
                    db.add(nowy_wpis)
                    raporty_dodane_count += 1

        db.commit()
        return {"status": "Sukces!",
                "wiadomosc": f"Zintegrowano i dodano {raporty_dodane_count} nowych rekordów analitycznych."}
    except Exception as e:
        db.rollback()
        return {"status": "blad", "wiadomosc": str(e)}


@app.get("/api/wykres/{gatunek}")
def pobierz_dane_wykresu(gatunek: str, user=Depends(jwt_auth.get_current_user), db: Session = Depends(get_db)):
    wyniki = db.query(RaportZintegrowany).filter(RaportZintegrowany.gatunek == gatunek).order_by(
        RaportZintegrowany.rok.asc()).all()

    return {
        "lata": [r.rok for r in wyniki],
        "zielen": [r.powierzchnia_parkow_ha for r in wyniki],
        "ptaki": [r.liczba_ptakow_api for r in wyniki]
    }
