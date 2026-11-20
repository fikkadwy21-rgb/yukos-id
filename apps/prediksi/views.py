from django.shortcuts import render
from .services import prediksi_harga_kos, get_ringkasan_dan_evaluasi, evaluasi_tarif_groq

def index(request):
    stats = get_ringkasan_dan_evaluasi()
    hasil_prediksi = None
    ulasan_ai = None
    input_user = {
        "jarak_km": 1.5,
        "rating": 4.2,
        "ac": "tidak",
    }

    if request.method == "POST":
        jarak_km = float(request.POST.get("jarak_km", 1.5))
        rating = float(request.POST.get("rating", 4.2))
        ac = request.POST.get("ac", "tidak")

        input_user = {
            "jarak_km": jarak_km,
            "rating": rating,
            "ac": ac,
        }
        hasil_prediksi = prediksi_harga_kos(jarak_km, rating, ac)
        ulasan_ai = evaluasi_tarif_groq(jarak_km, rating, ac, hasil_prediksi, stats)

    context = {
        "stats": stats,
        "hasil_prediksi": hasil_prediksi,
        "ulasan_ai": ulasan_ai,
        "input_user": input_user,
        "bar_values": [stats["rata_non_ac"], stats["rata_ac"]],
        "scatter_ac": stats["scatter_ac"],
        "scatter_non_ac": stats["scatter_non_ac"],
    }
    return render(request, "prediksi/index.html", context)
