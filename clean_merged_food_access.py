from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
OUTPUT_DIR = ROOT / "outputs"

FARA_XLSX = DOWNLOADS / "FoodAccessResearchAtlasData2019.xlsx"
FARA_CSV = ROOT / "Food Access Research Atlas.csv"
ACS_POP_CSV = DOWNLOADS / "ACSDT5Y2019.B01003-Data.csv"
ACS_HOUSING_CSV = DOWNLOADS / "ACSDT5Y2019.B25001-Data.csv"
FEA_XLSX = DOWNLOADS / "2025-food-environment-atlas-data.xlsx"

WIDE_OUTPUT = OUTPUT_DIR / "merged_food_access_clean_2019_wide.csv"
ANALYSIS_OUTPUT = OUTPUT_DIR / "merged_food_access_clean_2019_analysis.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "merged_food_access_cleaning_summary.txt"


def pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace({0: np.nan})
    return numerator / denominator * 100


def read_fara() -> pd.DataFrame:
    if FARA_XLSX.exists():
        df = pd.read_excel(FARA_XLSX, sheet_name="Food Access Research Atlas")
        source = FARA_XLSX
    elif FARA_CSV.exists():
        df = pd.read_csv(FARA_CSV)
        source = FARA_CSV
    else:
        raise FileNotFoundError("Could not find the FARA 2019 Excel or CSV source file.")

    df = df.copy()
    df["census_tract"] = df["CensusTract"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    df["county_fips"] = df["census_tract"].str[:5]
    df["fara_source_file"] = source.name
    return df


def read_acs_population() -> pd.DataFrame:
    df = pd.read_csv(ACS_POP_CSV, dtype=str)
    df = df.iloc[1:].copy()
    df["census_tract"] = df["GEO_ID"].str.replace("1400000US", "", regex=False)
    df["population_2019_acs"] = pd.to_numeric(df["B01003_001E"], errors="coerce")
    df["population_2019_moe_acs"] = pd.to_numeric(df["B01003_001M"], errors="coerce")
    df["acs_population_match_flag"] = True
    return df[["census_tract", "population_2019_acs", "population_2019_moe_acs", "acs_population_match_flag"]]


def read_acs_housing() -> pd.DataFrame:
    df = pd.read_csv(ACS_HOUSING_CSV, dtype=str)
    df = df.iloc[1:].copy()
    df["census_tract"] = df["GEO_ID"].str.replace("1400000US", "", regex=False)
    df["housing_units_2019_acs"] = pd.to_numeric(df["B25001_001E"], errors="coerce")
    df["housing_units_2019_moe_acs"] = pd.to_numeric(df["B25001_001M"], errors="coerce")
    df["acs_housing_match_flag"] = True
    return df[["census_tract", "housing_units_2019_acs", "housing_units_2019_moe_acs", "acs_housing_match_flag"]]


def read_food_environment() -> pd.DataFrame:
    stores = pd.read_excel(FEA_XLSX, sheet_name="STORES", skiprows=1)
    restaurants = pd.read_excel(FEA_XLSX, sheet_name="RESTAURANTS", skiprows=1)

    store_cols = [col for col in ["FIPS", "GROC20", "GROCPTH20"] if col in stores.columns]
    restaurant_cols = [col for col in ["FIPS", "FFR20", "FFRPTH20"] if col in restaurants.columns]

    food = stores[store_cols].merge(restaurants[restaurant_cols], on="FIPS", how="left")
    food["county_fips"] = food["FIPS"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    food = food.drop(columns=["FIPS"])

    numeric_cols = food.columns.difference(["county_fips"])
    food[numeric_cols] = food[numeric_cols].apply(pd.to_numeric, errors="coerce")
    food[numeric_cols] = food[numeric_cols].replace([-9999, -8888], np.nan)
    food = food.rename(
        columns={
            "GROC20": "grocery_stores_2020_county",
            "GROCPTH20": "grocery_stores_per_1000_2020_county",
            "FFR20": "fast_food_restaurants_2020_county",
            "FFRPTH20": "fast_food_restaurants_per_1000_2020_county",
        }
    )
    food["food_env_county_match_flag"] = True
    return food


def add_clean_variables(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()

    for flag in ["acs_population_match_flag", "acs_housing_match_flag", "food_env_county_match_flag"]:
        clean[flag] = clean[flag].fillna(False).astype(bool)

    clean["release_year"] = 2019
    clean["urban_rural"] = np.where(clean["Urban"].eq(1), "Urban", "Rural")

    clean["low_access_population_1_10"] = clean["LAPOP1_10"].fillna(0)
    clean["low_access_pct_1_10"] = pct(clean["low_access_population_1_10"], clean["Pop2010"])
    clean.loc[
        clean["low_access_pct_1_10"].between(100, 100.01, inclusive="right"),
        "low_access_pct_1_10",
    ] = 100

    clean["pct_low_income_population"] = pct(clean["TractLOWI"], clean["Pop2010"])
    clean["pct_white"] = pct(clean["TractWhite"], clean["Pop2010"])
    clean["pct_black"] = pct(clean["TractBlack"], clean["Pop2010"])
    clean["pct_asian"] = pct(clean["TractAsian"], clean["Pop2010"])
    clean["pct_native_hawaiian_pacific_islander"] = pct(clean["TractNHOPI"], clean["Pop2010"])
    clean["pct_american_indian_alaska_native"] = pct(clean["TractAIAN"], clean["Pop2010"])
    clean["pct_other_multiple_race"] = pct(clean["TractOMultir"], clean["Pop2010"])
    clean["pct_hispanic"] = pct(clean["TractHispanic"], clean["Pop2010"])

    clean["pct_no_vehicle_raw"] = pct(clean["TractHUNV"], clean["OHU2010"])
    clean["invalid_vehicle_pct_flag"] = (
        clean["pct_no_vehicle_raw"].lt(0)
        | clean["pct_no_vehicle_raw"].gt(100)
        | clean["pct_no_vehicle_raw"].isna()
    )
    clean["pct_no_vehicle"] = clean["pct_no_vehicle_raw"].where(~clean["invalid_vehicle_pct_flag"])

    clean["pct_snap_households"] = pct(clean["TractSNAP"], clean["OHU2010"])
    clean["population_change_pct_2010_to_2019"] = pct(
        clean["population_2019_acs"] - clean["Pop2010"], clean["Pop2010"]
    )
    clean["housing_units_change_pct_2010_to_2019"] = pct(
        clean["housing_units_2019_acs"] - clean["OHU2010"], clean["OHU2010"]
    )

    race_bins = [-0.01, 10, 20, 40, 100]
    race_labels = ["0-10%", "10-20%", "20-40%", "40-100%"]
    clean["black_pct_bin"] = pd.cut(clean["pct_black"], bins=race_bins, labels=race_labels)
    clean["hispanic_pct_bin"] = pd.cut(clean["pct_hispanic"], bins=race_bins, labels=race_labels)

    income_bins = [-np.inf, 40000, 65000, 100000, np.inf]
    income_labels = ["Under $40k", "$40k-$65k", "$65k-$100k", "$100k+"]
    clean["income_tier"] = pd.cut(clean["MedianFamilyIncome"], bins=income_bins, labels=income_labels)

    clean["missing_core_analysis_flag"] = clean[
        [
            "LA1and10",
            "low_access_pct_1_10",
            "PovertyRate",
            "MedianFamilyIncome",
            "pct_no_vehicle",
            "pct_black",
            "pct_hispanic",
            "Urban",
        ]
    ].isna().any(axis=1)

    clean["missing_merged_variables_flag"] = clean[
        [
            "population_2019_acs",
            "housing_units_2019_acs",
            "grocery_stores_2020_county",
            "fast_food_restaurants_2020_county",
        ]
    ].isna().any(axis=1)

    return clean


def build_analysis_dataset(wide: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "release_year",
        "census_tract",
        "county_fips",
        "State",
        "County",
        "Urban",
        "urban_rural",
        "Pop2010",
        "population_2019_acs",
        "population_2019_moe_acs",
        "acs_population_match_flag",
        "population_change_pct_2010_to_2019",
        "OHU2010",
        "housing_units_2019_acs",
        "housing_units_2019_moe_acs",
        "acs_housing_match_flag",
        "housing_units_change_pct_2010_to_2019",
        "GroupQuartersFlag",
        "PCTGQTRS",
        "LA1and10",
        "LILATracts_1And10",
        "low_access_population_1_10",
        "low_access_pct_1_10",
        "LowIncomeTracts",
        "PovertyRate",
        "MedianFamilyIncome",
        "income_tier",
        "HUNVFlag",
        "TractHUNV",
        "pct_no_vehicle",
        "pct_no_vehicle_raw",
        "invalid_vehicle_pct_flag",
        "pct_low_income_population",
        "pct_snap_households",
        "pct_white",
        "pct_black",
        "pct_asian",
        "pct_native_hawaiian_pacific_islander",
        "pct_american_indian_alaska_native",
        "pct_other_multiple_race",
        "pct_hispanic",
        "black_pct_bin",
        "hispanic_pct_bin",
        "grocery_stores_2020_county",
        "grocery_stores_per_1000_2020_county",
        "fast_food_restaurants_2020_county",
        "fast_food_restaurants_per_1000_2020_county",
        "food_env_county_match_flag",
        "missing_core_analysis_flag",
        "missing_merged_variables_flag",
    ]
    return wide[columns].rename(
        columns={
            "State": "state",
            "County": "county",
            "Urban": "urban",
            "Pop2010": "population_2010",
            "OHU2010": "occupied_housing_units_2010",
            "GroupQuartersFlag": "group_quarters_flag",
            "PCTGQTRS": "pct_group_quarters",
            "LA1and10": "low_access_status_1_10",
            "LILATracts_1And10": "low_income_low_access_status_1_10",
            "LowIncomeTracts": "low_income_tract",
            "PovertyRate": "poverty_rate",
            "MedianFamilyIncome": "median_family_income",
            "HUNVFlag": "low_vehicle_access_flag",
            "TractHUNV": "tract_households_no_vehicle",
        }
    )


def write_summary(wide: pd.DataFrame, analysis: pd.DataFrame, source_counts: dict) -> None:
    lines = [
        "Merged Food Access 2019 cleaning summary",
        f"FARA source rows: {source_counts['fara_rows']:,}",
        f"ACS population source rows: {source_counts['acs_pop_rows']:,}",
        f"ACS housing source rows: {source_counts['acs_housing_rows']:,}",
        f"Food Environment county rows: {source_counts['food_env_rows']:,}",
        f"Wide output rows: {len(wide):,}",
        f"Analysis output rows: {len(analysis):,}",
        "",
        "Join checks:",
        f"- Unmatched ACS population rows after tract join: {(~wide['acs_population_match_flag']).sum():,}",
        f"- Unmatched ACS housing rows after tract join: {(~wide['acs_housing_match_flag']).sum():,}",
        f"- Unmatched Food Environment county rows after county join: {(~wide['food_env_county_match_flag']).sum():,}",
        f"- Missing/NA grocery store values after replacing -9999/-8888: {wide['grocery_stores_2020_county'].isna().sum():,}",
        f"- Missing/NA fast-food values after replacing -9999/-8888: {wide['fast_food_restaurants_2020_county'].isna().sum():,}",
        "",
        "Cleaning choices:",
        "- Standardized CensusTract as an 11-character census_tract string before joins.",
        "- Created county_fips as the first five characters of census_tract.",
        "- Converted ACS estimates and margins of error to numeric values.",
        "- Replaced Food Environment Atlas -9999 and -8888 missing-value codes with NA.",
        "- Created low_access_pct_1_10 from LAPOP1_10 / Pop2010 * 100, treating blank LAPOP1_10 as zero for the derived percentage.",
        "- Created tract race/ethnicity percentages from tract counts divided by Pop2010.",
        "- Created pct_no_vehicle from TractHUNV / OHU2010 * 100; invalid or undefined values are flagged and set missing in pct_no_vehicle.",
        "- Created income_tier, black_pct_bin, hispanic_pct_bin, missing_core_analysis_flag, and missing_merged_variables_flag.",
        "",
        "Important warning:",
        "- Food Environment Atlas variables are county-level. After joining, every census tract in the same county has the same grocery/fast-food values.",
        "- These county-level variables can be used as context, but they should not replace tract-level predictors in the main research question.",
        "",
        "Missing/anomaly counts in analysis output:",
        f"- poverty_rate missing: {analysis['poverty_rate'].isna().sum():,}",
        f"- median_family_income missing: {analysis['median_family_income'].isna().sum():,}",
        f"- invalid_vehicle_pct_flag: {analysis['invalid_vehicle_pct_flag'].sum():,}",
        f"- missing_core_analysis_flag: {analysis['missing_core_analysis_flag'].sum():,}",
        f"- missing_merged_variables_flag: {analysis['missing_merged_variables_flag'].sum():,}",
        "",
        "Recommended first analysis filter:",
        "- Use missing_core_analysis_flag == False for the main EDA/model based on low access, race/ethnicity, income, vehicle access, and urban/rural status.",
    ]
    SUMMARY_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    fara = read_fara()
    acs_pop = read_acs_population()
    acs_housing = read_acs_housing()
    food_env = read_food_environment()

    wide = (
        fara.merge(acs_pop, on="census_tract", how="left")
        .merge(acs_housing, on="census_tract", how="left")
        .merge(food_env, on="county_fips", how="left")
    )
    wide = add_clean_variables(wide)
    analysis = build_analysis_dataset(wide)

    source_counts = {
        "fara_rows": len(fara),
        "acs_pop_rows": len(acs_pop),
        "acs_housing_rows": len(acs_housing),
        "food_env_rows": len(food_env),
    }

    wide.to_csv(WIDE_OUTPUT, index=False)
    analysis.to_csv(ANALYSIS_OUTPUT, index=False)
    write_summary(wide, analysis, source_counts)

    print(f"Wrote {WIDE_OUTPUT}")
    print(f"Wrote {ANALYSIS_OUTPUT}")
    print(f"Wrote {SUMMARY_OUTPUT}")
    print(SUMMARY_OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
