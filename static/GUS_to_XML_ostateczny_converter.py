import requests
import xml.etree.ElementTree as ET

BDL_BASE = "https://bdl.stat.gov.pl/api/v1"


def pobierz_gus_xml_lubelskie(lata):
    ID_LUBLIN = "060611163000"

    ZMIENNE_GUS = {
        73787: "parki spacerowo - wypoczynkowe",
        73788: "zieleńce",
        73789: "zieleń uliczna",
        73790: "tereny zieleni osiedlowej",
        73793: "cmentarze",
        73794: "lasy gminne"
    }

    root = ET.Element("Miasto", nazwa="Powiat m. Lublin", kod="0663000")

    kategorie_xml = {}
    for rok in lata:
        rok_elem = ET.SubElement(root, "Rok", wartosc=str(rok))
        kategorie_xml[rok] = {}
        for nazwa_kat in ZMIENNE_GUS.values():
            kat_elem = ET.SubElement(rok_elem, "Kategoria", nazwa=nazwa_kat)
            kat_elem.text = "0.00"
            kategorie_xml[rok][nazwa_kat] = kat_elem

    for var_id, nazwa_kat in ZMIENNE_GUS.items():
        url = f"{BDL_BASE}/data/by-unit/{ID_LUBLIN}"
        params = {
            "var-id": var_id,
            "format": "xml",
            "year": list(lata)
        }

        try:
            odpowiedz = requests.get(url, params=params, timeout=15)
            if odpowiedz.status_code == 200:
                gus_xml_tree = ET.fromstring(odpowiedz.content)

                for elem in gus_xml_tree.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]

                znaleziono_dane = False
                for year_val in gus_xml_tree.findall('.//yearVal'):
                    rok_elem_api = year_val.find('year')
                    val_elem_api = year_val.find('val')

                    if rok_elem_api is not None and val_elem_api is not None:
                        rok_api = int(rok_elem_api.text)
                        wartosc = float(val_elem_api.text)

                        if rok_api in kategorie_xml:
                            kategorie_xml[rok_api][nazwa_kat].text = str(wartosc)
                            znaleziono_dane = True

                if not znaleziono_dane:
                    print(
                        f"UWAGA: Pomyślnie pobrano XML z GUS dla '{nazwa_kat}', ale nie znaleziono w nim tagów <yearVal>!")

            else:
                print(f"[BŁĄD API] Status: {odpowiedz.status_code} dla {nazwa_kat}")

        except Exception as e:
            print(f"Błąd parsowania XML z GUS dla {nazwa_kat}: {e}")


    posortowane_lata = sorted(list(lata))
    for i in range(1, len(posortowane_lata)):
        rok_poprzedni = posortowane_lata[i - 1]
        rok_obecny = posortowane_lata[i]

        for nazwa_kat in ZMIENNE_GUS.values():
            wartosc_obecna = kategorie_xml[rok_obecny][nazwa_kat].text
            wartosc_poprzednia = kategorie_xml[rok_poprzedni][nazwa_kat].text

            if wartosc_obecna == "0.00" and wartosc_poprzednia != "0.00":
                kategorie_xml[rok_obecny][nazwa_kat].text = wartosc_poprzednia

    return root