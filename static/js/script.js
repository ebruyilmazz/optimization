window.onload = function() {
    // Şablondan veri al
    var labels = JSON.parse(document.getElementById('labelsData').textContent);
    var values = JSON.parse(document.getElementById('valuesData').textContent);

    var ctx = document.getElementById('maliyetGrafik').getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels, // Mağaza adları
            datasets: [{
                label: 'Maliyet',
                data: values, // Maliyet verileri
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
};
