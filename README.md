# Projekt Integracji Systemów - BirdData

## Autorzy
- Paweł Świeca
- Michał Szafranek

## Podział prac
- Paweł Świeca
  - Konfiguracja bazy danych
  - Budowa endpointów
  - Przygotowanie żądań do zasobów aplikacji od strony klienta
  - Wizualizacja danych w postaci wykresów

- Michał Szafranek
  - Przygotowanie panelu rejestracji i logowania
  - Implementacja zabezpieczeń ścieżek w postaci tokenów
  - Budowa struktury html i css aplikacji
  - Konfiguracja parsera danych GUS

## Wykorzystane technologie

W ramach projektu wykorzystano następujące rozwiązania:
### Backend

- Python 3.14
- Framework FastAPI
- Baza danych SQLite

### Frontend

- HTML, CSS, JS
- Silnik widoków Jinja2

Oprócz tego, do budowy aplikacji użyto bibliotek, wymienionych w pliku `requirements.txt`

## Opis projektu

Celem projektu jest zbadanie zależności między **zmianą powierzchni terenów zielonych** w Lublinie a 
zmianami **liczebności wybranych gatunków ptaków**. Aplikacja łączy się z niezależnymi źródłami danych takimi jak
serwer **API GUS** oraz repozytorium **GBIF**, by zintegrować określone dane i umieścić je w bazie danych. 
Sam panel aplikacji pozwala na **wizualizację** przykładowych danych dotyczących obserwacji całkowitej populacji ptaków
w określonym roku. Najistotniejszą funkcją jest **przygotowywanie wykresów** zależności między poszczególnymi powieszchniami terenów zielonych
(np. parki, zieleń osiedlowa, cmentarze) a ilością obserwacji wybranych gatunków ptaków (np. Wróbel domowy).


Zintegrowane, w wyniku działania aplikacji, dane dostarczają odpowiedzi na przykładowe pytania:

- Ile wynosi ogólna powierzchnia terenów zielonych w Lublinie, w 2024 roku?
- Jak zmieniała się powieszchnia zieleni osiedlowej w Lublinie w latach 2014-2024?
- Jak wygląda struktura procentowa poszczególnych rodzajów powieszchni zielonych w Lublinie?
- Ile unikalnych obserwacji ptaków zostało wykonanych w woj. Lubelskim w 2018 roku?
- Jakie gatunki ptaków były obserwowane woj. Lubelskim?
- Ile obserwacji sikorki bogatki zostało przeprowadzonych w Lublinie w 2020 roku?
- Jak zmieniała się tendencja obserwacji gęsi gęgawej w Lublinie w latach 2014-2024?


## Konfiguracja Środowiska

Projekt był uruchamiany na systemie `Windows 11`, przy pomocy programu `PyCharm 2026.1.2.` i wersji środowiska `Python 3.14.`

Uruchamianie projektu odbywało się poprzez uruchomienie pliku `main.py` za pomocą polecenia:
```
uvicorn main:app --reload
```

## Źródła danych

- **GBIF API** — Światowa Sieć Informacji o Bioróżnorodności. Została wykorzystana w celu pobierania informacji o wybranych gatunkach ptaków na terenie Lublina w formacie **JSON**.
- **GUS API** — baza Głównego Urzędu Statystycznego została wykorzystana w celu pobierania informacji na temat powierzchni terenów zielonych w obrębie Lublina w formacie **XML**.