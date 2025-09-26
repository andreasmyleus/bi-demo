// Dashboard JavaScript för Åland väderdata

let charts = {};
let currentData = [];

// Ladda data när sidan laddas
document.addEventListener('DOMContentLoaded', function() {
    loadLocations();
    loadInitialData();
});

// Ladda platser för filter
async function loadLocations() {
    try {
        const response = await fetch('/api/locations');
        const locations = await response.json();
        
        const locationSelect = document.getElementById('locationFilter');
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location.name;
            option.textContent = location.name;
            locationSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Fel vid laddning av platser:', error);
    }
}

// Ladda initial data
async function loadInitialData() {
    console.log('=== STARTAR LADDNING AV DATA ===');
    showLoading(true);
    
    // Timeout som automatiskt döljer spinner efter 5 sekunder
    const timeoutId = setTimeout(() => {
        console.log('⚠️ Timeout - döljer spinner automatiskt');
        showLoading(false);
    }, 5000);
    
    try {
        // Ladda väderdata först
        console.log('1. Laddar väderdata...');
        const weatherResponse = await fetch('/api/weather');
        if (!weatherResponse.ok) {
            throw new Error(`HTTP error! status: ${weatherResponse.status}`);
        }
        const weatherData = await weatherResponse.json();
        console.log('✓ Väderdata laddad:', weatherData.length, 'rader');
        
        // Ladda andra data
        console.log('2. Laddar statistik...');
        
        console.log('2a. Laddar temperaturstatistik...');
        let tempStats;
        try {
            const tempResponse = await fetch('/api/stats/temperature');
            tempStats = await tempResponse.json();
            console.log('✓ Temperaturstatistik laddad');
        } catch (error) {
            console.error('❌ Fel vid laddning av temperaturstatistik:', error);
            throw error;
        }
        
        console.log('2b. Laddar årstidsdata...');
        let seasonalData;
        try {
            const seasonalResponse = await fetch('/api/stats/seasonal');
            seasonalData = await seasonalResponse.json();
            console.log('✓ Årstidsdata laddad');
        } catch (error) {
            console.error('❌ Fel vid laddning av årstidsdata:', error);
            throw error;
        }
        
        console.log('2c. Laddar platsdata...');
        let locationData;
        try {
            const locationResponse = await fetch('/api/stats/locations');
            locationData = await locationResponse.json();
            console.log('✓ Platsdata laddad');
        } catch (error) {
            console.error('❌ Fel vid laddning av platsdata:', error);
            throw error;
        }
        
        console.log('✓ All statistik laddad');
        
        // Sätt data
        currentData = weatherData;
        console.log('3. Uppdaterar UI...');
        
        // Uppdatera komponenter
        updateStatsCards();
        updateWeatherTable(weatherData);
        
        // Skapa grafer med fallback-data om något saknas
        if (seasonalData && locationData) {
            createCharts(weatherData, seasonalData, locationData);
        } else {
            console.log('⚠️ Saknar data för grafer, skapar med tom data');
            createCharts(weatherData, [], []);
        }
        
        console.log('✓ All data laddad och UI uppdaterad!');
        
    } catch (error) {
        console.error('❌ Fel vid laddning av data:', error);
        alert(`Fel vid laddning av data: ${error.message}`);
    } finally {
        clearTimeout(timeoutId);
        console.log('=== SLUTAR LADDNING AV DATA ===');
        console.log('Döljer spinner...');
        showLoading(false);
        console.log('Spinner dold');
    }
}

// Visa/dölj laddningsspinner
function showLoading(show) {
    console.log('showLoading anropad med:', show);
    const spinner = document.getElementById('loadingSpinner');
    if (!spinner) {
        console.error('Spinner-element hittades inte!');
        return;
    }
    
    if (show) {
        spinner.classList.remove('hidden');
        console.log('Spinner visas');
    } else {
        spinner.classList.add('hidden');
        console.log('Spinner döljs');
    }
}

// Uppdatera statistik-kort
function updateStatsCards() {
    console.log('updateStatsCards anropad, currentData.length:', currentData.length);
    
    // Beräkna genomsnitt från aktuell data
    if (currentData.length > 0) {
        const avgTemp = currentData.reduce((sum, item) => sum + item.temperature_c, 0) / currentData.length;
        const avgHumidity = currentData.reduce((sum, item) => sum + item.humidity_percent, 0) / currentData.length;
        const avgWind = currentData.reduce((sum, item) => sum + item.wind_speed_ms, 0) / currentData.length;
        const totalPrecip = currentData.reduce((sum, item) => sum + item.precipitation_mm, 0);
        
        console.log('Beräknade värden:', { avgTemp, avgHumidity, avgWind, totalPrecip });
        
        const avgTempEl = document.getElementById('avgTemp');
        const avgHumidityEl = document.getElementById('avgHumidity');
        const avgWindEl = document.getElementById('avgWind');
        const totalPrecipEl = document.getElementById('totalPrecip');
        
        if (avgTempEl) avgTempEl.textContent = `${avgTemp.toFixed(1)}°C`;
        if (avgHumidityEl) avgHumidityEl.textContent = `${avgHumidity.toFixed(0)}%`;
        if (avgWindEl) avgWindEl.textContent = `${avgWind.toFixed(1)} m/s`;
        if (totalPrecipEl) totalPrecipEl.textContent = `${totalPrecip.toFixed(1)} mm`;
        
        console.log('Statistik-kort uppdaterade');
    } else {
        console.log('Ingen data att visa i statistik-kort');
    }
}

// Uppdatera väderdata-tabell
function updateWeatherTable(data) {
    const tbody = document.getElementById('weatherTableBody');
    tbody.innerHTML = '';
    
    data.slice(0, 50).forEach(item => { // Visa max 50 rader
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.date}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.location_name}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.temperature_c.toFixed(1)}°C</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.humidity_percent}%</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.wind_speed_ms.toFixed(1)} m/s ${item.wind_direction_text}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.precipitation_mm.toFixed(1)} mm</td>
        `;
        tbody.appendChild(row);
    });
}

// Skapa grafer
function createCharts(weatherData, seasonalData, locationData) {
    // Temperaturgraf
    createTemperatureChart(weatherData);
    
    // Luftfuktighetsgraf
    createHumidityChart(weatherData);
    
    // Årstidsgraf
    createSeasonalChart(seasonalData);
    
    // Platsgraf
    createLocationChart(locationData);
}

// Skapa temperaturgraf
function createTemperatureChart(data) {
    const ctx = document.getElementById('temperatureChart').getContext('2d');
    
    // Gruppera data per datum
    const groupedData = {};
    data.forEach(item => {
        if (!groupedData[item.date]) {
            groupedData[item.date] = [];
        }
        groupedData[item.date].push(item.temperature_c);
    });
    
    const dates = Object.keys(groupedData).sort();
    const avgTemps = dates.map(date => {
        const temps = groupedData[date];
        return temps.reduce((sum, temp) => sum + temp, 0) / temps.length;
    });
    
    if (charts.temperature) {
        charts.temperature.destroy();
    }
    
    charts.temperature = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.slice(-30), // Visa senaste 30 dagarna
            datasets: [{
                label: 'Genomsnittlig temperatur (°C)',
                data: avgTemps.slice(-30),
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Skapa luftfuktighetsgraf
function createHumidityChart(data) {
    const ctx = document.getElementById('humidityChart').getContext('2d');
    
    // Gruppera data per datum
    const groupedData = {};
    data.forEach(item => {
        if (!groupedData[item.date]) {
            groupedData[item.date] = [];
        }
        groupedData[item.date].push(item.humidity_percent);
    });
    
    const dates = Object.keys(groupedData).sort();
    const avgHumidity = dates.map(date => {
        const humidity = groupedData[date];
        return humidity.reduce((sum, hum) => sum + hum, 0) / humidity.length;
    });
    
    if (charts.humidity) {
        charts.humidity.destroy();
    }
    
    charts.humidity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.slice(-30),
            datasets: [{
                label: 'Genomsnittlig luftfuktighet (%)',
                data: avgHumidity.slice(-30),
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Skapa årstidsgraf
function createSeasonalChart(data) {
    const ctx = document.getElementById('seasonalChart').getContext('2d');
    
    if (charts.seasonal) {
        charts.seasonal.destroy();
    }
    
    charts.seasonal = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.season),
            datasets: [{
                label: 'Genomsnittlig temperatur (°C)',
                data: data.map(item => item.avg_temp),
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',   // Vår - grön
                    'rgba(245, 158, 11, 0.8)',  // Sommar - gul
                    'rgba(239, 68, 68, 0.8)',   // Höst - röd
                    'rgba(59, 130, 246, 0.8)'   // Vinter - blå
                ]
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Skapa platsgraf
function createLocationChart(data) {
    const ctx = document.getElementById('locationChart').getContext('2d');
    
    if (charts.location) {
        charts.location.destroy();
    }
    
    charts.location = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: 'Genomsnittlig temperatur (°C)',
                data: data.map(item => item.avg_temp),
                backgroundColor: 'rgba(59, 130, 246, 0.8)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Tillämpa filter
async function applyFilters() {
    showLoading(true);
    
    try {
        const filters = {
            location: document.getElementById('locationFilter').value,
            season: document.getElementById('seasonFilter').value,
            start_date: document.getElementById('startDateFilter').value,
            end_date: document.getElementById('endDateFilter').value
        };
        
        // Ta bort tomma filter
        const activeFilters = Object.fromEntries(
            Object.entries(filters).filter(([key, value]) => value !== '')
        );
        
        const queryParams = new URLSearchParams(activeFilters);
        const response = await fetch(`/api/weather?${queryParams}`);
        const data = await response.json();
        
        currentData = data;
        updateStatsCards();
        updateWeatherTable(data);
        
        // Uppdatera grafer med ny data
        const [seasonalData, locationData] = await Promise.all([
            fetch('/api/stats/seasonal').then(res => res.json()),
            fetch('/api/stats/locations').then(res => res.json())
        ]);
        
        createCharts(data, seasonalData, locationData);
        
    } catch (error) {
        console.error('Fel vid tillämpning av filter:', error);
        alert('Fel vid tillämpning av filter.');
    } finally {
        showLoading(false);
    }
}

// Rensa filter
function clearFilters() {
    document.getElementById('locationFilter').value = '';
    document.getElementById('seasonFilter').value = '';
    document.getElementById('startDateFilter').value = '';
    document.getElementById('endDateFilter').value = '';
    
    // Ladda om data utan filter
    loadInitialData();
}

// SQL Query funktioner
async function executeSqlQuery() {
    const query = document.getElementById('sqlQuery').value.trim();
    
    if (!query) {
        alert('Ange en SQL-fråga');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displaySqlResults(result);
        } else {
            alert(`SQL-fel: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Fel vid SQL-fråga:', error);
        alert('Fel vid körning av SQL-fråga');
    } finally {
        showLoading(false);
    }
}

function displaySqlResults(result) {
    const resultsDiv = document.getElementById('sqlResults');
    const rowCountSpan = document.getElementById('sqlRowCount');
    const table = document.getElementById('sqlResultsTable');
    
    // Visa antal rader
    rowCountSpan.textContent = `${result.row_count} rader returnerade`;
    
    if (result.data.length === 0) {
        table.innerHTML = '<tr><td colspan="100%" class="px-6 py-4 text-center text-gray-500">Inga resultat</td></tr>';
    } else {
        // Skapa tabellhuvud
        const thead = table.querySelector('thead');
        thead.innerHTML = '<tr></tr>';
        const headerRow = thead.querySelector('tr');
        
        result.columns.forEach(column => {
            const th = document.createElement('th');
            th.className = 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider';
            th.textContent = column;
            headerRow.appendChild(th);
        });
        
        // Skapa tabellkropp
        const tbody = table.querySelector('tbody');
        tbody.innerHTML = '';
        
        result.data.forEach(row => {
            const tr = document.createElement('tr');
            result.columns.forEach(column => {
                const td = document.createElement('td');
                td.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-900';
                td.textContent = row[column] !== null ? row[column] : '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }
    
    // Visa resultat
    resultsDiv.classList.remove('hidden');
}

function clearSqlResults() {
    document.getElementById('sqlQuery').value = '';
    document.getElementById('sqlResults').classList.add('hidden');
}

// Tvinga dölj spinner
function forceHideSpinner() {
    console.log('forceHideSpinner anropad - döljer spinner manuellt');
    showLoading(false);
}
