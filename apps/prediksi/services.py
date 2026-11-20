import os
import csv
from pathlib import Path
import numpy as np
import requests
from dotenv import load_dotenv
from django.conf import settings

load_dotenv(Path(settings.BASE_DIR) / ".env")

DATASET_PATH = Path(settings.BASE_DIR) / "dataset" / "kos_madiun.csv"

def load_dataset() -> list:
    rows = []
    with open(DATASET_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jarak_km = float(row["jarak_km"])
            rating = float(row["rating"])
            ac_num = 1 if row["ac"].strip().lower() == "ya" else 0
            harga_raw = float(row["harga"])
            harga_rp = int(round(harga_raw * 1000 if harga_raw < 10000 else harga_raw))
            rows.append({
                "jarak_km": jarak_km,
                "rating": rating,
                "ac_num": ac_num,
                "harga_rp": harga_rp,
            })
    return rows

def latih_ols(rows: list):
    X = np.array([[1.0, r["jarak_km"], r["rating"], float(r["ac_num"])] for r in rows])
    y = np.array([float(r["harga_rp"]) for r in rows])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta
    return beta, y, y_pred

def prediksi_harga_kos(jarak_km: float, rating: float, ac: str) -> int:
    rows = load_dataset()
    beta, _, _ = latih_ols(rows)
    ac_num = 1.0 if ac.lower() == "ya" else 0.0
    x_baru = np.array([1.0, float(jarak_km), float(rating), ac_num])
    hasil = float(x_baru @ beta)
    return int(round(hasil, -3))

def get_ringkasan_dan_evaluasi() -> dict:
    rows = load_dataset()
    _, y_true, y_pred = latih_ols(rows)

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    groq_siap = bool(api_key and not api_key.startswith("ganti_"))

    mae = int(round(float(np.mean(np.abs(y_true - y_pred)))))
    rmse = int(round(float(np.sqrt(np.mean((y_true - y_pred) ** 2)))))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2_val = 1.0 - (ss_res / ss_tot) if ss_tot else 0.0
    r2 = round(r2_val, 3)
    r2_persen = round(max(r2_val, 0.0) * 100, 1)

    harga_semua = [r["harga_rp"] for r in rows]
    harga_ac = [r["harga_rp"] for r in rows if r["ac_num"] == 1]
    harga_non_ac = [r["harga_rp"] for r in rows if r["ac_num"] == 0]

    rata_ac = int(round(float(np.mean(harga_ac)))) if harga_ac else 0
    rata_non_ac = int(round(float(np.mean(harga_non_ac)))) if harga_non_ac else 0
    selisih_ac = rata_ac - rata_non_ac
    persen_ac = round((selisih_ac / rata_non_ac) * 100, 1) if rata_non_ac else 0

    scatter_ac = []
    scatter_non_ac = []
    tabel_data = []

    for idx, r in enumerate(rows):
        item_scatter = {
            "x": r["jarak_km"],
            "y": r["harga_rp"],
            "rating": r["rating"],
        }
        if r["ac_num"] == 1:
            scatter_ac.append(item_scatter)
        else:
            scatter_non_ac.append(item_scatter)

        tabel_data.append({
            "no": idx + 1,
            "jarak_km": r["jarak_km"],
            "rating": r["rating"],
            "fasilitas": "Ber-AC" if r["ac_num"] == 1 else "Non-AC",
            "harga_rp": r["harga_rp"],
        })

    return {
        "groq_siap": groq_siap,
        "total_sampel": len(rows),
        "rata_rata_pasar": int(round(float(np.mean(harga_semua)))),
        "harga_min": int(min(harga_semua)),
        "harga_max": int(max(harga_semua)),
        "rata_ac": rata_ac,
        "rata_non_ac": rata_non_ac,
        "selisih_ac": selisih_ac,
        "persen_ac": persen_ac,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "r2_persen": r2_persen,
        "scatter_ac": scatter_ac,
        "scatter_non_ac": scatter_non_ac,
        "tabel_data": tabel_data,
    }

def evaluasi_tarif_groq(jarak_km: float, rating: float, ac: str, estimasi_rp: int, stats: dict) -> dict:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    fasilitas_label = "Ber-AC" if ac.lower() == "ya" else "Non-AC"
    acuan_kategori = stats["rata_ac"] if ac.lower() == "ya" else stats["rata_non_ac"]
    selisih_kategori = estimasi_rp - acuan_kategori

    status_wajar = "Kompetitif & Masuk Akal" if abs(selisih_kategori) <= 120000 else ("Di Atas Rata-rata Kategori" if selisih_kategori > 0 else "Sangat Terjangkau")
    fallback_teks = (
        f"Dengan jarak {jarak_km} km dari kampus, rating {rating}/5.0, dan fasilitas {fasilitas_label}, "
        f"estimasi Rp {estimasi_rp:,.0f}/bulan tergolong {status_wajar.lower()} dibandingkan rata-rata kos "
        f"{fasilitas_label} di Madiun (Rp {acuan_kategori:,.0f}/bulan). "
        f"Perlu diingat bahwa angka ini dihitung dari pola regresi linear 30 sampel data sehingga kondisi bangunan fisik tetap perlu dicek langsung."
    ).replace(",", ".")

    if not api_key or api_key.startswith("ganti_"):
        return {"sumber": "Analisis Statistik Lokal", "ulasan": fallback_teks}

    prompt = (
        f"Kamu adalah asisten penilai tarif kos mahasiswa di Kota Madiun. Berikan ulasan singkat (3-4 kalimat) "
        f"dalam Bahasa Indonesia yang objektif dan ramah mahasiswa.\n"
        f"- Spesifikasi input: Jarak ke kampus {jarak_km} km, Rating {rating}/5.0, Fasilitas {fasilitas_label}.\n"
        f"- Hasil prediksi Regresi Linear: Rp {estimasi_rp:,}/bulan.\n"
        f"- Rata-rata pasar Madiun: Rp {stats['rata_rata_pasar']:,}/bulan (Rata-rata {fasilitas_label}: Rp {acuan_kategori:,}/bulan).\n"
        f"Jelaskan apakah tarif tersebut wajar/kompetitif, faktor yang memengaruhinya, dan ingatkan keterbatasan model sampel 30 data."
    )

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 260,
            },
            timeout=10,
        )
        resp.raise_for_status()
        teks_ai = resp.json()["choices"][0]["message"]["content"].strip()
        return {"sumber": "Groq AI (Llama 3.3 70B)", "ulasan": teks_ai}
    except Exception:
        return {"sumber": "Analisis Statistik Lokal (Fallback)", "ulasan": fallback_teks}
