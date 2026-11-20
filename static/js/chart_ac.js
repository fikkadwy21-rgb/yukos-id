document.addEventListener("DOMContentLoaded", function () {
    const barValues = JSON.parse(document.getElementById("bar-values").textContent);
    const scatterAc = JSON.parse(document.getElementById("scatter-ac").textContent);
    const scatterNonAc = JSON.parse(document.getElementById("scatter-non-ac").textContent);

    Chart.defaults.color = "#d6c3c9";
    Chart.defaults.borderColor = "rgba(255, 255, 255, 0.08)";

    const barCtx = document.getElementById("barAcChart").getContext("2d");
    new Chart(barCtx, {
        type: "bar",
        data: {
            labels: ["Non-AC", "Ber-AC"],
            datasets: [{
                label: "Rata-rata Tarif (Rp)",
                data: barValues,
                backgroundColor: ["#7f2942", "#e11d48"],
                borderRadius: 8,
                barThickness: 54
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: val => "Rp " + val.toLocaleString("id-ID")
                    }
                }
            }
        }
    });

    const scatterCtx = document.getElementById("scatterJarakChart").getContext("2d");
    new Chart(scatterCtx, {
        type: "scatter",
        data: {
            datasets: [
                {
                    label: "Ber-AC",
                    data: scatterAc,
                    backgroundColor: "#fb7185",
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: "Non-AC",
                    data: scatterNonAc,
                    backgroundColor: "#f59e0b",
                    pointRadius: 6,
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            const p = ctx.raw;
                            return `${ctx.dataset.label}: ${p.x} km | Rating ${p.rating} | Rp ${p.y.toLocaleString("id-ID")}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "Jarak ke Kampus (km)" }
                },
                y: {
                    title: { display: true, text: "Tarif Bulanan (Rp)" },
                    ticks: {
                        callback: val => "Rp " + (val / 1000) + "k"
                    }
                }
            }
        }
    });
});
