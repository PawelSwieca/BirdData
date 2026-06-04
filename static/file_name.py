import re

def przygotuj_nazwe_pliku(gatunek: str, rozszerzenie: str):
    mapa_znakow = str.maketrans({
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ń": "n",
        "ó": "o",
        "ś": "s",
        "ż": "z",
        "ź": "z",
        "Ą": "A",
        "Ć": "C",
        "Ę": "E",
        "Ł": "L",
        "Ń": "N",
        "Ó": "O",
        "Ś": "S",
        "Ż": "Z",
        "Ź": "Z",
    })

    bez_polskich_znakow = gatunek.translate(mapa_znakow)
    bezpieczna_nazwa = re.sub(r"[^a-zA-Z0-9_-]+", "_", bez_polskich_znakow)

    return f"raport_{bezpieczna_nazwa}.{rozszerzenie}"