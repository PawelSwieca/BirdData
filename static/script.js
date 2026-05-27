const currentPath = window.location.pathname;
if (!localStorage.getItem("token") && currentPath !== "/login" && currentPath !== "/register") {
    window.location.href = "/login";
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            if (currentTheme === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }

            if (mojWykresInstance) {
                generujWykresAnalizy();
            }
        });
    }

    const globalLogoutBtn = document.getElementById('globalLogoutBtn');
    if (globalLogoutBtn && localStorage.getItem('token')) {
        globalLogoutBtn.style.display = 'inline-flex';
    }
});


function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
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


async function pobierzPtakiZBackendu() {
    const kontenerWynikow = document.getElementById('wynik-api');
    const wybranyRok = document.getElementById('input-rok').value;

    if (!wybranyRok || wybranyRok < 1800 || wybranyRok > 2025) {
        alert("Proszę wpisać poprawny rok!");
        return;
    }

    kontenerWynikow.innerHTML = `<div class="msg"><em>Łączenie z GBIF API i pobieranie danych dla roku ${wybranyRok}... 🌍</em></div>`;

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch(`/api/ptaki/${wybranyRok}`);
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);

        const dane = await odpowiedz.json();

        let listHTML = dane.przykladowe_ptaki.map(ptak => `
            <li>
                <span><strong>Gatunek:</strong> ${ptak.gatunek || "Nieznany"}</span>
                <span class="api-month-badge">Miesiąc: ${ptak.miesiac || "?"}</span>
            </li>
        `).join('');


        kontenerWynikow.innerHTML = `
            <div class="api-summary-card">
                <span class="number">${dane.laczna_liczba_obserwacji_w_api}</span>
                <span class="label">Obserwacji ptaków w woj. lubelskim w ${wybranyRok} roku</span>
            </div>
            <h4>Przykładowe 5 rekordów z JSON-a:</h4>
            <ul class="api-list">
                ${listHTML}
            </ul>
        `;
    } catch (error) {
        kontenerWynikow.innerHTML = `<div class="msg msg-error"><b>BŁĄD:</b> ${error.message}</div>`;
    }
}


async function uruchomIntegracje() {
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;

    btn.innerHTML = "Trwa analityczna integracja danych...";
    btn.style.pointerEvents = "none";

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch('/api/integruj_i_zapisz', { method: 'POST' });
        if (!odpowiedz.ok) throw new Error(`Błąd serwera: ${odpowiedz.status}`);
        const dane = await odpowiedz.json();

        if (dane.status === "Sukces!") {
            btn.innerHTML = `Baza zaktualizowana!`;
            btn.style.background = "var(--success-border)";
            btn.style.color = "#787200"
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.background = "";
                btn.style.color = "var(--text-main)";
                btn.style.pointerEvents = "auto";
            }, 3000);
        } else {
            throw new Error(dane.wiadomosc);
        }
    } catch (error) {
        alert(`BŁĄD: ${error.message}`);
        btn.innerHTML = originalText;
        btn.style.pointerEvents = "auto";
    }
}


let mojWykresInstance = null;

async function generujWykresAnalizy() {
    let msgContainer = document.getElementById('chart-msg');
    if (!msgContainer) {
        msgContainer = document.createElement('div');
        msgContainer.id = 'chart-msg';
        document.getElementById('canvasWykresu').parentElement.prepend(msgContainer);
    }

    const wybranyGatunek = document.getElementById('select-ptak').value;
    msgContainer.innerHTML = `<div class="msg"><em>Pobieranie danych o gatunku: <b>${wybranyGatunek}</b> z bazy SQLite...</em></div>`;

    try {
        const odpowiedz = await wykonajAutoryzowanyFetch(`/api/wykres/${wybranyGatunek}`);
        if (!odpowiedz.ok) throw new Error("Brak danych w bazie! Najpierw uruchom integrację (zakładka Baza Danych).");

        const daneZ_Bazy = await odpowiedz.json();

        if (daneZ_Bazy.lata.length === 0) {
            throw new Error("Baza danych jest pusta. Uruchom najpierw integrację danych.");
        }

        msgContainer.innerHTML = ``;

        if (mojWykresInstance) {
            mojWykresInstance.destroy();
        }


        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#a7a9be' : '#636e72';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

        const ctx = document.getElementById('canvasWykresu').getContext('2d');
        mojWykresInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: daneZ_Bazy.lata,
                datasets: [
                    {
                        label: 'Powierzchnia parków (ha)',
                        data: daneZ_Bazy.zielen,
                        borderColor: '#2f8f4e',
                        backgroundColor: 'rgba(47, 143, 78, 0.1)',
                        yAxisID: 'y-zielen',
                        tension: 0.3,
                        borderWidth: 3,
                        fill: true
                    },
                    {
                        label: `Liczba obserwacji ptaka`,
                        data: daneZ_Bazy.ptaki,
                        borderColor: '#7a5cff',
                        backgroundColor: 'rgba(122, 92, 255, 0.1)',
                        yAxisID: 'y-ptaki',
                        tension: 0.3,
                        borderWidth: 3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                color: textColor,
                plugins: {
                    legend: { labels: { color: textColor } }
                },
                scales: {
                    x: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    'y-zielen': {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Hektary [ha]', color: '#2f8f4e' },
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    'y-ptaki': {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'Liczba rekordów w GBIF', color: '#7a5cff' },
                        ticks: { color: textColor },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });

        const kontenerEksportu = document.getElementById('kontener-eksportu');
        const btnEksportXML = document.getElementById('btn-eksport-xml');
        const btnEksportJSON = document.getElementById('btn-eksport-json');


        kontenerEksportu.style.display = 'flex';

        btnEksportXML.onclick = async () => {
            btnEksportXML.innerText = "Generowanie pliku...";
            try {
                const odpEksport = await wykonajAutoryzowanyFetch(`/api/eksport/xml/${wybranyGatunek}`);
                if (!odpEksport.ok) throw new Error("Błąd podczas eksportu");


                const plikBlob = await odpEksport.blob();


                const urlPobierania = window.URL.createObjectURL(plikBlob);
                const a = document.createElement('a');
                a.href = urlPobierania;
                a.download = `raport_${wybranyGatunek.replace(/\s+/g, '_')}.xml`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(urlPobierania);

                btnEksportXML.innerText = "Pobrano!";
                setTimeout(() => btnEksportXML.innerText = "Pobierz te dane jako XML", 2000);
            } catch (error) {
                alert(error.message);
                btnEksportXML.innerText = "Pobierz te dane jako XML";
            }
        };

        btnEksportJSON.onclick = async () => {
            btnEksportJSON.innerText = "Generowanie...";
            try {
                const odpEksport = await wykonajAutoryzowanyFetch(`/api/eksport/json/${wybranyGatunek}`);
                if (!odpEksport.ok) throw new Error("Błąd podczas eksportu JSON");

                const plikBlob = await odpEksport.blob();
                const urlPobierania = window.URL.createObjectURL(plikBlob);
                const a = document.createElement('a');
                a.href = urlPobierania;
                a.download = `raport_${wybranyGatunek.replace(/\s+/g, '_')}.json`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(urlPobierania);

                btnEksportJSON.innerText = "Pobrano JSON!";
                setTimeout(() => btnEksportJSON.innerText = "Pobierz JSON", 2000);
            } catch (error) {
                alert(error.message);
                btnEksportJSON.innerText = "Pobierz JSON";
            }
        };

    } catch (error) {
        msgContainer.innerHTML = `<div class="msg msg-error"><b>BŁĄD WYKRESU:</b> ${error.message}</div>`;
    }
}