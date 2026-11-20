import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
csv_path = BASE_DIR / "kos_madiun.csv"
model_path = BASE_DIR / "model_kos.joblib"

df = pd.read_csv(csv_path)
df["ac_num"] = df["ac"].map({"ya": 1, "tidak": 0})

X = df[["jarak_km", "rating", "ac_num"]]
y = df["harga"]

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, model_path)
print("Sukses! Model tersimpan di:", model_path)
print("Koefisien model:", model.coef_.round(2))
