// --- Funkcja pomocnicza do wysyłania tokenu JWT ---
async function wykonajAutoryzowanyFetch(url, opcje = {}) {
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Brak dostępu! Zaloguj się ponownie.");
        window.location.href = "/login";
        throw new Error("Brak tokenu autoryzacji");
    }

    const domyslneOpcje = {
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    };

    const odpowiedz = await fetch(url, { ...domyslneOpcje, ...opcje });

    // Jeśli token wygasł, przenieś do logowania
    if (odpowiedz.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        throw new Error("Sesja wygasła");
    }

    return odpowiedz;
}

// ----------------------------------------------------

async function pobierzPtakiZBackendu() {
    const kontenerWynikow = document.getElementById('wynik-api');
    kontenerWynikow.innerHTML = "<p><em>Łączenie z backendem FastAPI i pobieranie ptaków...</em></p>";

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch('/api/ptaki/2020');
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);

        const dane = await odpowiedz.json();
        let htmlDoWstawienia = `
            <h4 style="color: blue;">${dane.wiadomosc}</h4>
            <p><b>Łącznie w bazie GBIF:</b> ${dane.laczna_liczba_obserwacji_w_api} obserwacji</p>
            <h5>Przykładowe 5 ptaków:</h5><ul>
        `;
        dane.przykladowe_ptaki.forEach(ptak => {
            htmlDoWstawienia += `<li><b>${ptak.gatunek}</b> (miesiąc: ${ptak.miesiac})</li>`;
        });
        kontenerWynikow.innerHTML = htmlDoWstawienia + `</ul>`;
    } catch (error) {
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD:</b> ${error.message}</p>`;
    }
}

async function uruchomIntegracje() {
    const kontenerWynikow = document.getElementById('wynik-api');
    kontenerWynikow.innerHTML = "<p><em>Trwa integracja danych (XML+REST) z bezpiecznym zapisem do SQLite...</em></p>";

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch('/api/integruj_i_zapisz', { method: 'POST' });
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);

        const dane = await odpowiedz.json();
        if (dane.status === "Sukces!") {
            let info = dane.dodane_lata.length > 0
                ? `Dodano wpisy dla lat: ${dane.dodane_lata.join(', ')}`
                : "Baza jest już aktualna.";
            kontenerWynikow.innerHTML = `
                <h4 style="color: #2f8f4e;">Integracja zakończona pomyślnie!</h4>
                <p><b>Informacja ORM:</b> ${info}</p>
                <p><i>Utworzono plik "baza_projektowa.db".</i></p>`;
        } else {
            throw new Error(dane.wiadomosc);
        }
    } catch (error) {
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD INTEGRACJI:</b> ${error.message}</p>`;
    }
}

async function filtrujWybranePtaki() {
    const kontenerWynikow = document.getElementById('wynik-api');
    kontenerWynikow.innerHTML = "<p><em>Szukam kaczek w bazie GBIF...</em></p>";

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch('/api/ptaki/2020/Anas platyrhynchos');
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);

        const dane = await odpowiedz.json();
        let htmlDoWstawienia = `
            <h4 style="color: #2f8f4e;">${dane.wiadomosc}</h4>
            <p><b>Ilość znalezionych kaczek krzyżówek w tym roku:</b> ${dane.laczna_liczba_obserwacji_w_api}</p>
            <h5>Przykładowe obserwacje z API:</h5><ul>
        `;
        dane.przykladowe_ptaki.forEach(ptak => {
            htmlDoWstawienia += `<li>Gatunek: <b>${ptak.gatunek}</b> (miesiąc: ${ptak.miesiac})</li>`;
        });
        kontenerWynikow.innerHTML = htmlDoWstawienia + `</ul>`;
    } catch (error) {
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD:</b> ${error.message}</p>`;
    }
}