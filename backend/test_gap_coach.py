from gap_coach import load_model, suggest_data_gaps
import pandas as pd

model, features = load_model()
df = pd.read_csv("data/synthetic_alt_credit_data.csv")

df["thinness"] = (
    (df["has_rent_data"] == 0).astype(int)
    + (df["utility_payment_punctuality_score"] < df["utility_payment_punctuality_score"].quantile(0.1)).astype(int)
    + (df["subscription_payment_consistency"] < df["subscription_payment_consistency"].quantile(0.1)).astype(int)
)

sample = df.sort_values("thinness", ascending=False).iloc[0][features].to_dict()
suggestions = suggest_data_gaps(model, features, sample, df)

print("Suggestions for a more severely thin-file user:\n")
for s in suggestions:
    print(f"  {s['data_source']}: +{s['estimated_score_uplift']} points "
          f"({s['current_score']} -> {s['potential_score']})")