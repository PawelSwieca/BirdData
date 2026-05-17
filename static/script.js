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