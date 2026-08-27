from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path.home() / "Downloads" / "food_access_clean_2019_M.csv"
OUTPUT_DIR = ROOT / "outputs" / "eda_graphs"
OUTPUT_PATH = OUTPUT_DIR / "grouped_boxplot_race_bins_income_tier_low_access.png"


def main() -> None:
    mpl.rcParams["text.parse_math"] = False
    sns.set_theme(style="whitegrid", context="notebook")

    df = pd.read_csv(DATA_PATH)
    df = df[df["missing_core_analysis_flag"].eq(False)].copy()

    income_order = ["Under $40k", "$40k-$65k", "$65k-$100k", "$100k+"]
    race_order = ["0-10%", "10-20%", "20-40%", "40-100%"]

    palette = {
        "Under $40k": "#8c2d04",
        "$40k-$65k": "#d95f0e",
        "$65k-$100k": "#2b8cbe",
        "$100k+": "#31a354",
    }

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), sharey=True)

    panels = [
        ("black_pct_bin", "Black population (% of tract)", "Black population bins"),
        ("hispanic_pct_bin", "Hispanic population (% of tract)", "Hispanic population bins"),
    ]

    for ax, (race_col, xlabel, title) in zip(axes, panels):
        plot_df = df.dropna(subset=[race_col, "income_tier", "low_access_pct_1_10"]).copy()
        plot_df[race_col] = pd.Categorical(plot_df[race_col], categories=race_order, ordered=True)
        plot_df["income_tier"] = pd.Categorical(
            plot_df["income_tier"], categories=income_order, ordered=True
        )

        sns.boxplot(
            data=plot_df,
            x=race_col,
            y="low_access_pct_1_10",
            hue="income_tier",
            order=race_order,
            hue_order=income_order,
            palette=palette,
            fliersize=0.6,
            linewidth=0.9,
            ax=ax,
        )

        ax.set_title(title, fontsize=13, weight="bold")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Low-access population (%)" if ax is axes[0] else "")
        ax.set_ylim(0, 105)
        ax.tick_params(axis="x", rotation=0)
        ax.grid(axis="y", alpha=0.35)
        ax.grid(axis="x", visible=False)
        ax.legend_.remove()

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        title="Median family income tier",
        loc="upper center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.91),
    )

    fig.suptitle(
        "Low Food Access by Race/Ethnicity Composition and Income Tier",
        fontsize=15,
        weight="bold",
        y=0.98,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.84])
    OUTPUT_DIR.mkdir(exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
