async function pobierzPtakiZBackendu() {

    const kontenerWynikow = document.getElementById('wynik-api');


    kontenerWynikow.innerHTML = "<p><em>Łączenie z backendem FastAPI i pobieranie ptaków z GBIF... 🦅</em></p>";

    try {

        const rokTestowy = 2020;


        const url = `/api/ptaki/${rokTestowy}`;
        const odpowiedz = await fetch(url);


        if (!odpowiedz.ok) {
            throw new Error(`Błąd serwera: ${odpowiedz.status}`);
        }


        const dane = await odpowiedz.json();


        console.log("Dane odebrane z Pythona:", dane);


        let htmlDoWstawienia = `
            <h4 style="color: blue;">${dane.wiadomosc}</h4>
            <p><b>Łącznie w bazie GBIF:</b> ${dane.laczna_liczba_obserwacji_w_api} obserwacji</p>
            <h5>Przykładowe 5 ptaków:</h5>
            <ul>
        `;


        dane.przykladowe_ptaki.forEach(ptak => {
            htmlDoWstawienia += `<li><b>${ptak.gatunek}</b> (zaobserwowano w miesiącu: ${ptak.miesiac})</li>`;
        });

        htmlDoWstawienia += `</ul>`;


        kontenerWynikow.innerHTML = htmlDoWstawienia;

    } catch (error) {

        console.error("Wystąpił błąd:", error);
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD:</b> ${error.message}</p>`;
    }
}

async function uruchomIntegracje() {
    const kontenerWynikow = document.getElementById('wynik-api');
    kontenerWynikow.innerHTML = "<p><em>Trwa integracja danych z XML i API oraz bezpieczny zapis (SERIALIZABLE) do bazy SQLite za pomocą ORM... ⚙️</em></p>";

    try {
        const odpowiedz = await fetch('/api/integruj_i_zapisz', { method: 'POST' });

        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);

        const dane = await odpowiedz.json();
        console.log("Wynik integracji:", dane);

        if (dane.status === "Sukces!") {
            let info = dane.dodane_lata.length > 0
                ? `Dodano nowe wpisy do bazy dla lat: ${dane.dodane_lata.join(', ')}`
                : "Baza jest już aktualna (dane były zintegrowane wcześniej).";

            kontenerWynikow.innerHTML = `
                <h4 style="color: #2f8f4e;">Integracja i zapis do bazy zakończone pomyślnie!</h4>
                <p><b>Informacja ORM:</b> ${info}</p>
                <p><i>Zajrzyj do folderu projektu – powstał tam fizyczny plik bazy danych "baza_projektowa.db".</i></p>
            `;
        } else {
            throw new Error(dane.wiadomosc);
        }

    } catch (error) {
        console.error("Wystąpił błąd:", error);
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD INTEGRACJI:</b> ${error.message}</p>`;
    }
}