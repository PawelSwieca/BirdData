async function pobierzPtakiZBackendu() {
    const kontenerWynikow = document.getElementById('wynik-api');

    const wybranyRok = document.getElementById('input-rok').value;

    if (!wybranyRok || wybranyRok < 1800 || wybranyRok > 2025) {
        alert("Proszę wpisać poprawny rok!");
        return;
    }

    kontenerWynikow.innerHTML = `<p><em>Łączenie z GBIF API i pobieranie danych dla roku ${wybranyRok}...</em></p>`;

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch(`/api/ptaki/${wybranyRok}`);
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);

        const dane = await odpowiedz.json();

        let htmlDoWstawienia = `
            <h4 style="color: #007bb5;">Sukces! Połączono z bazą zewnętrzną.</h4>
            <p><b>Łączna liczba zarejestrowanych obserwacji wszystkich ptaków w woj. lubelskim w ${wybranyRok} roku:</b> ${dane.laczna_liczba_obserwacji_w_api}</p>
            <h5>Przykładowe 5 rekordów z JSON-a:</h5>
            <ul>
        `;

        dane.przykladowe_ptaki.forEach(ptak => {
            htmlDoWstawienia += `<li>Gatunek: <b>${ptak.gatunek || "Nieznany"}</b> (Zgłoszono w miesiącu nr: ${ptak.miesiac || "?"})</li>`;
        });

        kontenerWynikow.innerHTML = htmlDoWstawienia + `</ul>`;
    } catch (error) {
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD:</b> ${error.message}</p>`;
    }
}

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
    if (odpowiedz.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        throw new Error("Sesja wygasła");
    }
    return odpowiedz;
}


let mojWykresInstance = null;

async function uruchomIntegracje() {
    const kontenerWynikow = document.getElementById('wynik-api');
    kontenerWynikow.innerHTML = "<p><em>Trwa analityczna integracja danych (XML + 3 Gatunki z REST API) w bazie danych...</em></p>";
    try {
        const odpowiedz = await wykonajAutoryzowanyFetch('/api/integruj_i_zapisz', { method: 'POST' });
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);
        const dane = await odpowiedz.json();

        if (dane.status === "Sukces!") {
            kontenerWynikow.innerHTML = `<h4 style="color: #2f8f4e;">Baza zaktualizowana!</h4><p>${dane.wiadomosc}</p>`;
        } else {
            throw new Error(dane.wiadomosc);
        }
    } catch (error) {
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD:</b> ${error.message}</p>`;
    }
}


async function generujWykresAnalizy() {
    const kontenerWynikow = document.getElementById('wynik-api');

    const wybranyGatunek = document.getElementById('select-ptak').value;

    kontenerWynikow.innerHTML = `<p><em>Pobieranie (Import) danych o gatunku: <b>${wybranyGatunek}</b> z bazy SQLite...</em></p>`;

    try {

        const odpowiedz = await wykonajAutoryzowanyFetch(`/api/wykres/${wybranyGatunek}`);
        if (!odpowiedz.ok) throw new Error("Brak danych w bazie! Najpierw kliknij fioletowy przycisk integracji.");

        const daneZ_Bazy = await odpowiedz.json();

        if (daneZ_Bazy.lata.length === 0) {
            throw new Error("Baza danych jest pusta. Uruchom najpierw integrację danych plików.");
        }


        kontenerWynikow.innerHTML = `<h4>Wykres trendu dla: ${wybranyGatunek} (Dane zaimportowane z SQLite)</h4>`;


        if (mojWykresInstance) {
            mojWykresInstance.destroy();
        }


        const ctx = document.getElementById('canvasWykresu').getContext('2d');
        mojWykresInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: daneZ_Bazy.lata,
                datasets: [
                    {
                        label: 'Powierzchnia parków (ha) ',
                        data: daneZ_Bazy.zielen,
                        borderColor: '#2f8f4e',
                        backgroundColor: 'rgba(47, 143, 78, 0.1)',
                        yAxisID: 'y-zielen',
                        tension: 0.2
                    },
                    {
                        label: `Liczba obserwacji ptaka `,
                        data: daneZ_Bazy.ptaki,
                        borderColor: '#7a5cff',
                        backgroundColor: 'rgba(122, 92, 255, 0.1)',
                        yAxisID: 'y-ptaki',
                        tension: 0.2
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    'y-zielen': {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Hektary [ha]', color: '#2f8f4e' }
                    },
                    'y-ptaki': {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'Liczba rekordów w GBIF', color: '#7a5cff' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });

    } catch (error) {
        kontenerWynikow.innerHTML = `<p style="color: red;"><b>BŁĄD WYKRESU:</b> ${error.message}</p>`;
    }
}