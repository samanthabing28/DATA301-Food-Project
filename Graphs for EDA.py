from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

mpl.rcParams["text.parse_math"] = False #stops "$" in tier labels being read as LaTeX

DATA_PATH = Path(__file__).resolve().parent / "food_access_clean_2019_M.csv" #Makes this code universal (this part from claude)
df = pd.read_csv(DATA_PATH)

#Plot 1: Poverty rate vs low acces
df_plot1 = df.dropna(subset=["poverty_rate", "low_access_pct_1_10"])

plt.figure(figsize=(8, 6))
plt.scatter(df_plot1["poverty_rate"], df_plot1["low_access_pct_1_10"], alpha=0.15, s=8, color="steelblue")

plt.xlabel("Poverty Rate (%)")
plt.ylabel("Low Access Population (%, 1 mile urban / 10 mile rural)")
plt.title("Poverty Rate vs Low Food Access by Census Tract")

plt.tight_layout()
plt.show()
plt.savefig(Path(__file__).resolve().parent / "Poverty Rate vs Low Food Access by Census Tract.png", dpi=150)

#Plot 2: Low access by race bin, split by income tier
income_order = ["Under $40k", "$40k-$65k", "$65k-$100k", "$100k+"]
race_order = ["0-10%", "10-20%", "20-40%", "40-100%"]
income_colors = {
    "Under $40k": "firebrick",
    "$40k-$65k": "darkorange",
    "$65k-$100k": "seagreen",
    "$100k+": "steelblue",
}

for race_col, race_label in [("black_pct_bin", "Black"), ("hispanic_pct_bin", "Hispanic")]:
    plotdf = df.dropna(subset=[race_col, "income_tier", "low_access_pct_1_10"])

    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=plotdf,
        x=race_col,
        y="low_access_pct_1_10",
        hue="income_tier",
        order=race_order,
        hue_order=income_order,
        palette=income_colors,
        fliersize=1,
    )

    plt.xlabel(f"{race_label} Population (% of tract)")
    plt.ylabel("Low Access Population (%)")
    plt.title(f"Low Food Access by {race_label} Population Bin, Split by Income Tier")
    plt.legend(title="Income Tier", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    plt.show()
    plt.savefig(Path(__file__).resolve().parent / f"Low Food Access by {race_label} Population Bin.png", dpi=150)