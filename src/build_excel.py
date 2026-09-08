"""Build excel/opportunity_scoring.xlsx as a live model, not a report of results.

The workbook is a working scoring model. Weights sit in one labelled, highlighted input block on
the Assumptions sheet and every downstream cell - normalization, contributions, score, rank,
sensitivity and the recommendation band - is an Excel formula that points at that block. Change
a weight and the ranking moves. Nothing computed by the Python scorer is pasted in as a value.

The formulas reproduce src/score.py exactly: min-max within year, competitive intensity
inverted, weighted sum, and bands applied to the mean score over the forward window.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
WEIGHTS_PATH = ROOT / "config" / "weights.yaml"
OUTPUT_PATH = ROOT / "excel" / "opportunity_scoring.xlsx"

DISCLOSURE = (
    "Illustrative dataset constructed to be directionally consistent with publicly reported "
    "industry estimates. Figures are for methodology demonstration and are not market research."
)

# Fixed factor order. Every sheet lays factors out in this order, so a weight column and a
# normalized-value row can be multiplied together positionally by SUMPRODUCT.
FACTORS = [
    ("serviceable_market_size", "Serviceable market size", "G", False),
    ("cagr", "CAGR", "E", False),
    ("design_services_addressability", "Design-services addressability", "F", False),
    ("strategic_fit", "Strategic fit", "K", False),
    ("customer_demand", "Customer demand", "I", False),
    ("competitive_intensity", "Competitive intensity", "H", True),
    ("entry_feasibility", "Entry feasibility", "J", False),
]

RAW_HEADERS = [
    ("segment_id", 12),
    ("segment_name", 38),
    ("year", 8),
    ("market_size_usd_bn", 18),
    ("cagr_pct", 11),
    ("design_services_addressable_pct", 30),
    ("serviceable_market_usd_bn", 24),
    ("competitive_intensity", 20),
    ("customer_demand", 17),
    ("entry_feasibility", 17),
    ("strategic_fit", 14),
    ("talent_availability", 19),
    ("design_cycle_months", 19),
]

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
INPUT_FILL = PatternFill("solid", fgColor="FFE699")
BAND_FILL = PatternFill("solid", fgColor="F2F2F2")
HEADER_FONT = Font(color="FFFFFF", bold=True)
TITLE_FONT = Font(bold=True, size=14)
NOTE_FONT = Font(italic=True, size=9, color="595959")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

FIRST_ROW = 2  # data starts on row 2 on every grid sheet


def style_header(sheet, row: int, headers: list[str]) -> None:
    for column, label in enumerate(headers, start=1):
        cell = sheet.cell(row=row, column=column, value=label)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def add_footnote(sheet, row: int) -> None:
    cell = sheet.cell(row=row, column=1, value=DISCLOSURE)
    cell.font = NOTE_FONT


def build_assumptions(sheet, config: dict, profile_names: list[str], n_rows: int) -> None:
    sheet["A1"] = "Opportunity scoring model - assumptions and inputs"
    sheet["A1"].font = TITLE_FONT
    sheet["A2"] = DISCLOSURE
    sheet["A2"].font = NOTE_FONT

    sheet["A4"] = "Weights (yellow cells are inputs - edit these and every sheet recalculates)"
    sheet["A4"].font = Font(bold=True)

    headers = ["Factor", "Direction"] + [config["profiles"][p]["label"] for p in profile_names]
    style_header(sheet, 6, headers)

    inverted = set(config["inverted_factors"])
    for offset, (key, label, _raw_column, _inv) in enumerate(FACTORS):
        row = 7 + offset
        sheet.cell(row=row, column=1, value=label).border = BOX
        direction = "Inverted (crowded is worse)" if key in inverted else "Higher is better"
        sheet.cell(row=row, column=2, value=direction).border = BOX
        for index, profile in enumerate(profile_names):
            cell = sheet.cell(row=row, column=3 + index)
            cell.value = config["profiles"][profile]["weights"][key]
            cell.fill = INPUT_FILL
            cell.border = BOX
            cell.number_format = "0%"

    total_row = 7 + len(FACTORS)
    sheet.cell(row=total_row, column=1, value="Total").font = Font(bold=True)
    for index in range(len(profile_names)):
        column = get_column_letter(3 + index)
        cell = sheet.cell(row=total_row, column=3 + index)
        cell.value = f"=SUM({column}7:{column}{total_row - 1})"
        cell.number_format = "0%"
        cell.font = Font(bold=True)
    # Rounded before comparing: a column of decimal weights summed in binary floating point is
    # not reliably exactly 1, and a false alarm on this cell would undermine the whole workbook.
    last_weight_column = get_column_letter(2 + len(profile_names))
    sheet.cell(row=total_row, column=3 + len(profile_names)).value = (
        f"=IF(SUMPRODUCT(--(ROUND(C{total_row}:{last_weight_column}{total_row},6)<>1))=0,"
        f"\"All profiles sum to 100%\",\"CHECK: a profile no longer sums to 100%\")"
    )
    sheet.cell(row=total_row, column=3 + len(profile_names)).font = Font(bold=True)

    band_row = total_row + 2
    sheet.cell(row=band_row, column=1, value="Recommendation bands and window").font = Font(bold=True)
    band_inputs = [
        ("Prioritize if forward mean score is at least", config["bands"]["prioritize_min"], "0.0"),
        ("Selective if forward mean score is at least", config["bands"]["selective_min"], "0.0"),
        ("Forward window - first year", config["forward_window"]["start_year"], "0"),
        ("Forward window - last year", config["forward_window"]["end_year"], "0"),
    ]
    for offset, (label, value, fmt) in enumerate(band_inputs):
        row = band_row + 1 + offset
        sheet.cell(row=row, column=1, value=label).border = BOX
        cell = sheet.cell(row=row, column=3, value=value)
        cell.fill = INPUT_FILL
        cell.border = BOX
        cell.number_format = fmt

    method_row = band_row + 7
    sheet.cell(row=method_row, column=1, value="Method").font = Font(bold=True)
    method_notes = [
        "1. Serviceable market = TAM x design-services addressable share. The model scores on "
        "serviceable market, never on raw TAM.",
        "2. Every factor is min-max normalized to 0-100 across the eight segments within each "
        "year, so a score states relative standing in that year.",
        "3. Competitive intensity is inverted after normalization, so a high contribution means "
        "an uncrowded segment.",
        "4. Score = sum of normalized factor x weight. Weights live only in the yellow block "
        "above and in config/weights.yaml.",
        "5. The recommendation band is applied to the mean score over the forward window, not to "
        "a single year.",
        f"6. The grid sheets carry {n_rows} segment-year rows (8 segments x 10 years, 2021-2030).",
    ]
    for offset, note in enumerate(method_notes):
        cell = sheet.cell(row=method_row + 1 + offset, column=1, value=note)
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    sheet.column_dimensions["A"].width = 48
    sheet.column_dimensions["B"].width = 28
    for index in range(len(profile_names) + 1):
        sheet.column_dimensions[get_column_letter(3 + index)].width = 22

    return {
        "weight_columns": {
            profile: get_column_letter(3 + index) for index, profile in enumerate(profile_names)
        },
        "weight_first_row": 7,
        "weight_last_row": total_row - 1,
        "prioritize_cell": f"$C${band_row + 1}",
        "selective_cell": f"$C${band_row + 2}",
        "window_start_cell": f"$C${band_row + 3}",
        "window_end_cell": f"$C${band_row + 4}",
    }


def build_raw(sheet, fact: pd.DataFrame, dim: pd.DataFrame) -> None:
    style_header(sheet, 1, [name for name, _ in RAW_HEADERS])
    names = dim.set_index("segment_id")["segment_name"]

    for offset, row in enumerate(fact.itertuples(index=False)):
        r = FIRST_ROW + offset
        sheet.cell(row=r, column=1, value=row.segment_id)
        sheet.cell(row=r, column=2, value=names[row.segment_id])
        sheet.cell(row=r, column=3, value=int(row.year))
        sheet.cell(row=r, column=4, value=row.market_size_usd_bn).number_format = "#,##0.0"
        sheet.cell(row=r, column=5, value=row.cagr_pct).number_format = "0.00"
        sheet.cell(row=r, column=6, value=row.design_services_addressable_pct).number_format = "0.0%"
        # The definitional line of the whole model, kept as a formula so it is visible.
        sheet.cell(row=r, column=7, value=f"=D{r}*F{r}").number_format = "#,##0.00"
        sheet.cell(row=r, column=8, value=row.competitive_intensity).number_format = "0.0"
        sheet.cell(row=r, column=9, value=row.customer_demand).number_format = "0.0"
        sheet.cell(row=r, column=10, value=row.entry_feasibility).number_format = "0.0"
        sheet.cell(row=r, column=11, value=row.strategic_fit).number_format = "0.0"
        sheet.cell(row=r, column=12, value=row.talent_availability).number_format = "0.0"
        sheet.cell(row=r, column=13, value=row.design_cycle_months).number_format = "0.0"

    for index, (_name, width) in enumerate(RAW_HEADERS, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "D2"
    add_footnote(sheet, FIRST_ROW + len(fact) + 1)


def build_normalization(sheet, n_rows: int) -> None:
    last = FIRST_ROW + n_rows - 1
    headers = ["segment_id", "segment_name", "year"] + [f"norm_{key}" for key, _, _, _ in FACTORS]
    style_header(sheet, 1, headers)

    for offset in range(n_rows):
        r = FIRST_ROW + offset
        sheet.cell(row=r, column=1, value=f"='Raw Data'!A{r}")
        sheet.cell(row=r, column=2, value=f"='Raw Data'!B{r}")
        sheet.cell(row=r, column=3, value=f"='Raw Data'!C{r}")

        for index, (_key, _label, raw_column, inverted) in enumerate(FACTORS):
            value_ref = f"'Raw Data'!{raw_column}{r}"
            year_range = f"'Raw Data'!$C${FIRST_ROW}:$C${last}"
            data_range = f"'Raw Data'!${raw_column}${FIRST_ROW}:${raw_column}${last}"
            low = f"MINIFS({data_range},{year_range},$C{r})"
            high = f"MAXIFS({data_range},{year_range},$C{r})"
            # IFERROR catches a zero spread: the factor cannot discriminate that year, so every
            # segment sits mid-scale. Matches the fillna(50) branch in src/score.py.
            scaled = f"IFERROR(({value_ref}-{low})/({high}-{low})*100,50)"
            formula = f"=100-{scaled}" if inverted else f"={scaled}"
            cell = sheet.cell(row=r, column=4 + index, value=formula)
            cell.number_format = "0.0"

    sheet.column_dimensions["A"].width = 12
    sheet.column_dimensions["B"].width = 38
    sheet.column_dimensions["C"].width = 8
    for index in range(len(FACTORS)):
        sheet.column_dimensions[get_column_letter(4 + index)].width = 26
    sheet.freeze_panes = "D2"
    add_footnote(sheet, last + 2)


def build_scoring(sheet, n_rows: int, layout: dict) -> None:
    last = FIRST_ROW + n_rows - 1
    base_column = layout["weight_columns"]["base"]
    headers = (
        ["segment_id", "segment_name", "year"]
        + [f"contrib_{key}" for key, _, _, _ in FACTORS]
        + ["opportunity_score", "rank_in_year"]
    )
    style_header(sheet, 1, headers)

    score_column = get_column_letter(4 + len(FACTORS))
    for offset in range(n_rows):
        r = FIRST_ROW + offset
        sheet.cell(row=r, column=1, value=f"=Normalization!A{r}")
        sheet.cell(row=r, column=2, value=f"=Normalization!B{r}")
        sheet.cell(row=r, column=3, value=f"=Normalization!C{r}")

        for index in range(len(FACTORS)):
            norm_cell = f"Normalization!{get_column_letter(4 + index)}{r}"
            weight_cell = f"Assumptions!${base_column}${layout['weight_first_row'] + index}"
            cell = sheet.cell(row=r, column=4 + index, value=f"={norm_cell}*{weight_cell}")
            cell.number_format = "0.0"

        first_contrib = get_column_letter(4)
        last_contrib = get_column_letter(3 + len(FACTORS))
        score_cell = sheet.cell(
            row=r, column=4 + len(FACTORS), value=f"=SUM({first_contrib}{r}:{last_contrib}{r})"
        )
        score_cell.number_format = "0.0"

        # Rank within the year, computed without sorting: count the segments in the same year
        # scoring higher, add one. RANK.EQ cannot be conditioned on the year.
        sheet.cell(
            row=r,
            column=5 + len(FACTORS),
            value=(
                f"=SUMPRODUCT(($C${FIRST_ROW}:$C${last}=$C{r})*"
                f"(${score_column}${FIRST_ROW}:${score_column}${last}>${score_column}{r}))+1"
            ),
        )

    sheet.column_dimensions["A"].width = 12
    sheet.column_dimensions["B"].width = 38
    sheet.column_dimensions["C"].width = 8
    for index in range(len(FACTORS) + 2):
        sheet.column_dimensions[get_column_letter(4 + index)].width = 24
    sheet.freeze_panes = "D2"
    add_footnote(sheet, last + 2)


def build_sensitivity(sheet, n_rows: int, layout: dict, config: dict, profiles: list[str]) -> None:
    last = FIRST_ROW + n_rows - 1
    labels = [config["profiles"][p]["label"] for p in profiles]
    headers = (
        ["segment_id", "segment_name", "year"]
        + [f"Score - {label}" for label in labels]
        + [f"Rank - {label}" for label in labels]
    )
    style_header(sheet, 1, headers)

    weight_first = layout["weight_first_row"]

    for offset in range(n_rows):
        r = FIRST_ROW + offset
        sheet.cell(row=r, column=1, value=f"=Normalization!A{r}")
        sheet.cell(row=r, column=2, value=f"=Normalization!B{r}")
        sheet.cell(row=r, column=3, value=f"=Normalization!C{r}")

        for index, profile in enumerate(profiles):
            weight_column = layout["weight_columns"][profile]
            # Written out term by term rather than as SUMPRODUCT. The normalized values lie
            # across a row and the weights down a column, and Excel returns #VALUE! when
            # SUMPRODUCT is handed arrays of different orientation.
            terms = "+".join(
                f"Normalization!{get_column_letter(4 + k)}{r}"
                f"*Assumptions!${weight_column}${weight_first + k}"
                for k in range(len(FACTORS))
            )
            cell = sheet.cell(row=r, column=4 + index, value=f"={terms}")
            cell.number_format = "0.0"

        for index in range(len(profiles)):
            score_column = get_column_letter(4 + index)
            sheet.cell(
                row=r,
                column=4 + len(profiles) + index,
                value=(
                    f"=SUMPRODUCT(($C${FIRST_ROW}:$C${last}=$C{r})*"
                    f"(${score_column}${FIRST_ROW}:${score_column}${last}>${score_column}{r}))+1"
                ),
            )

    sheet.column_dimensions["A"].width = 12
    sheet.column_dimensions["B"].width = 38
    sheet.column_dimensions["C"].width = 8
    for index in range(len(profiles) * 2):
        sheet.column_dimensions[get_column_letter(4 + index)].width = 22
    sheet.freeze_panes = "D2"
    add_footnote(sheet, last + 2)


def build_ranking(sheet, dim: pd.DataFrame, n_rows: int, layout: dict, profiles: list[str],
                  config: dict, model_year: int) -> None:
    last = FIRST_ROW + n_rows - 1
    score_column = get_column_letter(4 + len(FACTORS))
    rank_column = get_column_letter(5 + len(FACTORS))

    sheet["A1"] = "Ranking and recommendation"
    sheet["A1"].font = TITLE_FONT
    sheet["A2"] = DISCLOSURE
    sheet["A2"].font = NOTE_FONT

    sheet["A4"] = "Model year (input - change it to re-rank any year 2021-2030)"
    sheet["A4"].font = Font(bold=True)
    year_cell = sheet["D4"]
    year_cell.value = model_year
    year_cell.fill = INPUT_FILL
    year_cell.border = BOX

    header_row = 6
    labels = [config["profiles"][p]["label"] for p in profiles]
    headers = (
        ["segment_id", "segment_name", "Score in model year", "Rank in model year",
         "Forward mean score", "Recommendation"]
        + [f"Rank - {label}" for label in labels]
        + ["Max rank swing vs house view"]
    )
    style_header(sheet, header_row, headers)

    segments = dim["segment_id"].tolist()
    for offset, segment_id in enumerate(segments):
        r = header_row + 1 + offset
        sheet.cell(row=r, column=1, value=segment_id).border = BOX
        sheet.cell(row=r, column=2, value=f"=VLOOKUP($A{r},'Raw Data'!$A${FIRST_ROW}:$B${last},2,FALSE)")

        criteria = (
            f"'Scoring Model'!$A${FIRST_ROW}:$A${last},$A{r},"
            f"'Scoring Model'!$C${FIRST_ROW}:$C${last},$D$4"
        )
        cell = sheet.cell(
            row=r, column=3,
            value=f"=SUMIFS('Scoring Model'!${score_column}${FIRST_ROW}:${score_column}${last},{criteria})",
        )
        cell.number_format = "0.0"
        sheet.cell(
            row=r, column=4,
            value=f"=SUMIFS('Scoring Model'!${rank_column}${FIRST_ROW}:${rank_column}${last},{criteria})",
        )

        # The band is applied to the window mean, exactly as src/score.py does it.
        window_criteria = (
            f"'Scoring Model'!$A${FIRST_ROW}:$A${last},$A{r},"
            f"'Scoring Model'!$C${FIRST_ROW}:$C${last},\">=\"&Assumptions!{layout['window_start_cell']},"
            f"'Scoring Model'!$C${FIRST_ROW}:$C${last},\"<=\"&Assumptions!{layout['window_end_cell']}"
        )
        mean_cell = sheet.cell(
            row=r, column=5,
            value=(
                f"=AVERAGEIFS('Scoring Model'!${score_column}${FIRST_ROW}:${score_column}${last},"
                f"{window_criteria})"
            ),
        )
        mean_cell.number_format = "0.0"
        sheet.cell(
            row=r, column=6,
            value=(
                f'=IF($E{r}>=Assumptions!{layout["prioritize_cell"]},"Prioritize",'
                f'IF($E{r}>=Assumptions!{layout["selective_cell"]},"Selective","Deprioritize"))'
            ),
        ).font = Font(bold=True)

        for index in range(len(profiles)):
            sensitivity_column = get_column_letter(4 + len(profiles) + index)
            sheet.cell(
                row=r, column=7 + index,
                value=(
                    f"=SUMIFS(Sensitivity!${sensitivity_column}${FIRST_ROW}:${sensitivity_column}${last},"
                    f"Sensitivity!$A${FIRST_ROW}:$A${last},$A{r},"
                    f"Sensitivity!$C${FIRST_ROW}:$C${last},$D$4)"
                ),
            )

        # Compared column by column: ABS does not aggregate over a range, and the alternative
        # profiles are the columns after the house view.
        swings = ",".join(
            f"ABS($G{r}-{get_column_letter(8 + index)}{r})" for index in range(len(profiles) - 1)
        )
        sheet.cell(row=r, column=7 + len(profiles), value=f"=MAX({swings})")

    note_row = header_row + len(segments) + 2
    sheet.cell(row=note_row, column=1, value=(
        "Reading this sheet: a segment whose rank barely moves across the four profile columns is "
        "ranked by the data. One that swings two or more places is ranked by the weights, and the "
        "recommendation for it should be argued on its own merits rather than on the score."
    )).alignment = Alignment(wrap_text=True, vertical="top")
    add_footnote(sheet, note_row + 2)

    sheet.column_dimensions["A"].width = 12
    sheet.column_dimensions["B"].width = 38
    for index in range(3, 8 + len(profiles)):
        sheet.column_dimensions[get_column_letter(index)].width = 21


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with WEIGHTS_PATH.open() as handle:
        config = yaml.safe_load(handle)

    dim = pd.read_csv(PROCESSED_DIR / "dim_segment.csv")
    fact = pd.read_csv(PROCESSED_DIR / "fact_segment_year.csv")
    n_rows = len(fact)
    model_year = int(config["forward_window"]["end_year"])

    # Base profile first so it occupies the leftmost weight column and reads as the house view.
    profiles = [config["base_profile"]] + [
        name for name in config["profiles"] if name != config["base_profile"]
    ]

    workbook = Workbook()
    raw_sheet = workbook.active
    raw_sheet.title = "Raw Data"
    normalization_sheet = workbook.create_sheet("Normalization")
    scoring_sheet = workbook.create_sheet("Scoring Model")
    sensitivity_sheet = workbook.create_sheet("Sensitivity")
    ranking_sheet = workbook.create_sheet("Ranking")
    assumptions_sheet = workbook.create_sheet("Assumptions")

    layout = build_assumptions(assumptions_sheet, config, profiles, n_rows)
    build_raw(raw_sheet, fact, dim)
    build_normalization(normalization_sheet, n_rows)
    build_scoring(scoring_sheet, n_rows, layout)
    build_sensitivity(sensitivity_sheet, n_rows, layout, config, profiles)
    build_ranking(ranking_sheet, dim, n_rows, layout, profiles, config, model_year)

    for profile in profiles:
        column = layout["weight_columns"][profile]
        workbook.defined_names.add(
            DefinedName(
                f"weights_{profile}",
                attr_text=(
                    f"Assumptions!${column}${layout['weight_first_row']}:"
                    f"${column}${layout['weight_last_row']}"
                ),
            )
        )

    workbook.active = workbook.index(ranking_sheet)
    workbook.save(OUTPUT_PATH)
    print(f"workbook: {OUTPUT_PATH} ({len(workbook.sheetnames)} sheets, {n_rows} modelled rows)")


if __name__ == "__main__":
    main()
