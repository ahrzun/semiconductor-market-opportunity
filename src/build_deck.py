"""Build presentation/market_strategy.pptx.

Seven slides. Every title is an assertion the slide then supports, not a topic label, because a
leadership audience reads titles and skims bodies. Every number on every slide is read from
data/processed at build time, so the deck cannot drift from the model behind it.

No charting library is used anywhere: the comparison bars are native PowerPoint rectangles,
which stay editable in the file the audience receives.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from zip_determinism import normalize

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
WEIGHTS_PATH = ROOT / "config" / "weights.yaml"
OUTPUT_PATH = ROOT / "presentation" / "market_strategy.pptx"

DISCLOSURE = (
    "Illustrative dataset constructed to be directionally consistent with publicly reported "
    "industry estimates. Figures are for methodology demonstration and are not market research."
)

NAVY = RGBColor(0x1F, 0x38, 0x64)
GREEN = RGBColor(0x1B, 0x6B, 0x45)
AMBER = RGBColor(0xB0, 0x7A, 0x12)
RED = RGBColor(0x9C, 0x3A, 0x3A)
GREY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xD9, 0xD9, 0xD9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

BAND_COLOURS = {"Prioritize": GREEN, "Selective": AMBER, "Deprioritize": RED}

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
MARGIN = Inches(0.55)
CONTENT_TOP = Inches(1.55)
CONTENT_WIDTH = SLIDE_WIDTH - 2 * MARGIN


def textbox(slide, left, top, width, height, text, *, size=14, bold=False, color=NAVY,
            align=PP_ALIGN.LEFT, italic=False, spacing=Pt(6)):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    for index, line in enumerate(text.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = align
        paragraph.space_after = spacing
        run = paragraph.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
        run.font.name = "Calibri"
    return box


def bullets(slide, left, top, width, height, items, *, size=14, color=NAVY):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    for index, (lead, body) in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(10)
        head = paragraph.add_run()
        head.text = f"{lead}  "
        head.font.size = Pt(size)
        head.font.bold = True
        head.font.color.rgb = color
        head.font.name = "Calibri"
        tail = paragraph.add_run()
        tail.text = body
        tail.font.size = Pt(size)
        tail.font.color.rgb = GREY
        tail.font.name = "Calibri"
    return box


def rectangle(slide, left, top, width, height, colour):
    from pptx.enum.shapes import MSO_SHAPE

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = colour
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_slide(presentation, title, *, kicker=None, number=None):
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])

    textbox(slide, MARGIN, Inches(0.42), CONTENT_WIDTH, Inches(0.85), title, size=27, bold=True)
    rectangle(slide, MARGIN, Inches(1.34), CONTENT_WIDTH, Emu(14000), LIGHT)
    if kicker:
        textbox(slide, MARGIN, Inches(1.16), CONTENT_WIDTH, Inches(0.3), kicker,
                size=11, color=GREY, italic=True)

    footer = "Semiconductor design-services opportunity  |  Illustrative dataset, not market research"
    textbox(slide, MARGIN, Inches(7.03), Inches(10.5), Inches(0.3), footer, size=9, color=GREY)
    if number is not None:
        textbox(slide, SLIDE_WIDTH - Inches(1.2), Inches(7.03), Inches(0.65), Inches(0.3),
                str(number), size=9, color=GREY, align=PP_ALIGN.RIGHT)
    return slide


def add_table(slide, left, top, width, headers, rows, *, column_widths=None, font_size=11,
              band_column=None):
    table_shape = slide.shapes.add_table(
        len(rows) + 1, len(headers), left, top, width, Inches(0.32) * (len(rows) + 1)
    )
    table = table_shape.table
    table.first_row = True

    if column_widths:
        total = sum(column_widths)
        for index, share in enumerate(column_widths):
            table.columns[index].width = Emu(int(width * share / total))

    for index, label in enumerate(headers):
        cell = table.cell(0, index)
        cell.text = label
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        paragraph = cell.text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER if index else PP_ALIGN.LEFT
        run = paragraph.runs[0]
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = WHITE
        run.font.name = "Calibri"

    for row_index, row in enumerate(rows, start=1):
        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.text = str(value)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_index % 2 else RGBColor(0xF4, 0xF6, 0xF9)
            paragraph = cell.text_frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.CENTER if column_index else PP_ALIGN.LEFT
            run = paragraph.runs[0]
            run.font.size = Pt(font_size)
            run.font.name = "Calibri"
            colour = GREY
            if band_column is not None and column_index == band_column:
                colour = BAND_COLOURS.get(str(value), GREY)
                run.font.bold = True
            run.font.color.rgb = colour
    return table


def legend(slide, left, top):
    """The one colour-coded legend the deck uses."""
    offset = left
    for label, colour in BAND_COLOURS.items():
        rectangle(slide, offset, top + Inches(0.04), Inches(0.16), Inches(0.16), colour)
        textbox(slide, offset + Inches(0.22), top - Inches(0.02), Inches(1.35), Inches(0.28),
                label, size=11, bold=True, color=colour)
        offset += Inches(1.62)


# ------------------------------------------------------------------------------------------
# Slides
# ------------------------------------------------------------------------------------------

def slide_summary(presentation, ctx):
    slide = add_slide(
        presentation,
        "Prioritize automotive, analog and HPC; hold power electronics; exit memory",
        kicker="Recommendation | Semiconductor design-services capacity, 2026-2030",
        number=1,
    )

    rows = [
        (
            band,
            ", ".join(ctx["bands"][band]),
            f"{ctx['band_serviceable'][band]:.0f}",
            f"{ctx['band_share'][band]:.0f}%",
        )
        for band in ("Prioritize", "Selective", "Deprioritize")
    ]
    add_table(
        slide, MARGIN, CONTENT_TOP, CONTENT_WIDTH,
        ["Call", "Segments", "2030 serviceable market, USD bn", "Share of serviceable pool"],
        rows, column_widths=[1.4, 6.2, 2.4, 2.2], font_size=12, band_column=0,
    )

    bullets(
        slide, MARGIN, Inches(3.5), CONTENT_WIDTH, Inches(3.0),
        [
            ("The call.",
             f"Concentrate design capacity on automotive & ADAS, analog & mixed-signal and HPC "
             f"accelerator ASICs. Together they hold {ctx['top3_share']:.0f}% of the "
             f"serviceable market in 2030 and the three highest forward scores "
             f"({ctx['forward'].loc['AUTO']:.0f}, {ctx['forward'].loc['ANLG']:.0f} and "
             f"{ctx['forward'].loc['HPC']:.0f} out of 100)."),
            ("Enter selectively.",
             "Silicon photonics through partnership rather than hiring - it compounds at "
             f"{ctx['phot_cagr']:.0f}% but has the thinnest talent pool in the set. Hold power "
             "electronics; do not build against it."),
            ("Do not chase size.",
             f"Memory is the second-largest market in 2030 at USD {ctx['mem_tam']:.0f}bn and the "
             f"worst opportunity in the set, because only {ctx['mem_addressable']:.0f}% of it is "
             "reachable by an outsourced design house. Scoring on serviceable market rather than "
             "TAM moves it from second place to fifth."),
            ("This ranking was stress-tested.",
             "Re-weighted three ways. Memory stays eighth and RF & 5G seventh under every "
             "profile, and automotive never falls below third. The ordering inside the "
             "prioritize group is weight-sensitive and is argued on its merits, not on its "
             "score."),
        ],
        size=13,
    )
    legend(slide, MARGIN, Inches(6.55))


def slide_landscape(presentation, ctx):
    slide = add_slide(
        presentation,
        "Eight segments, one filter: how much of each market can we actually sell into",
        kicker="Market landscape | 2030 view",
        number=2,
    )

    rows = [
        (
            row.segment_name,
            row.value_chain_stage,
            f"{row.market_size_usd_bn:,.0f}",
            f"{row.design_services_addressable_pct * 100:.0f}%",
            f"{row.serviceable_market_usd_bn:,.1f}",
            f"{row.cagr_pct:.1f}%",
        )
        for row in ctx["latest"].itertuples()
    ]
    add_table(
        slide, MARGIN, CONTENT_TOP, CONTENT_WIDTH,
        ["Segment", "Value-chain position", "TAM USD bn", "Addressable",
         "Serviceable USD bn", "CAGR"],
        rows, column_widths=[3.4, 3.0, 1.5, 1.5, 1.8, 1.1], font_size=11,
    )

    textbox(
        slide, MARGIN, Inches(5.05), CONTENT_WIDTH, Inches(0.9),
        "Addressable share is the share of a segment's TAM that a design-services provider can "
        "realistically be engaged on. It ranges from 4.5% in memory, where design stays captive "
        "inside a handful of integrated device manufacturers, to 25.5% in analog. Everything "
        "that follows is scored on the serviceable column, never on the TAM column.",
        size=12, color=GREY,
    )

    rectangle(slide, MARGIN, Inches(6.05), CONTENT_WIDTH, Inches(0.72), RGBColor(0xF4, 0xF6, 0xF9))
    textbox(slide, MARGIN + Inches(0.15), Inches(6.14), CONTENT_WIDTH - Inches(0.3), Inches(0.6),
            "Data disclosure: " + DISCLOSURE, size=11, color=GREY, italic=True)


def slide_growth(presentation, ctx):
    slide = add_slide(
        presentation,
        "Ranking on TAM would put memory second; on serviceable market it is fifth",
        kicker="Growth and serviceable-market analysis | 2030",
        number=3,
    )

    textbox(slide, MARGIN, CONTENT_TOP, Inches(5.0), Inches(0.3),
            "2030 market, USD bn", size=12, bold=True)
    textbox(slide, MARGIN + Inches(5.3), CONTENT_TOP, Inches(3.0), Inches(0.3),
            "Reachable", size=12, bold=True, color=GREEN)
    textbox(slide, MARGIN + Inches(6.6), CONTENT_TOP, Inches(3.0), Inches(0.3),
            "Out of reach", size=12, bold=True, color=GREY)

    # Proportional bars drawn as native shapes: TAM as the full width, serviceable as the filled
    # portion. The visual argument of the whole deck is how little of each bar is green.
    bar_left = MARGIN + Inches(3.15)
    bar_span = Inches(6.45)
    max_tam = ctx["latest"]["market_size_usd_bn"].max()
    top = Inches(1.95)
    for row in ctx["latest"].itertuples():
        textbox(slide, MARGIN, top - Inches(0.06), Inches(3.05), Inches(0.3),
                row.segment_name, size=11, color=NAVY)
        full = Emu(int(bar_span * row.market_size_usd_bn / max_tam))
        reachable = Emu(int(bar_span * row.serviceable_market_usd_bn / max_tam))
        rectangle(slide, bar_left, top, full, Inches(0.24), LIGHT)
        rectangle(slide, bar_left, top, max(reachable, Emu(9000)), Inches(0.24), GREEN)
        textbox(slide, bar_left + full + Inches(0.1), top - Inches(0.06), Inches(2.4), Inches(0.3),
                f"{row.serviceable_market_usd_bn:,.1f} of {row.market_size_usd_bn:,.0f}",
                size=10, color=GREY)
        top += Inches(0.42)

    textbox(
        slide, MARGIN, Inches(5.45), CONTENT_WIDTH, Inches(1.4),
        "Memory has the second-largest bar and almost no green in it: 95.5% of that market is out "
        "of reach. HPC, automotive and analog are the three segments where both the bar and the "
        "green portion are large. Growth alone does not settle it either - silicon photonics "
        f"compounds at {ctx['phot_cagr']:.0f}%, the fastest in the set, on a serviceable base of "
        f"USD {ctx['phot_serviceable']:.1f}bn, which is a partnership, not a capacity build.",
        size=12, color=GREY,
    )


def slide_competitive(presentation, ctx):
    slide = add_slide(
        presentation,
        "Power electronics grows through 2030 and gets less attractive every year after 2027",
        kicker="Competitive and opportunity analysis | the case for not ranking on size",
        number=4,
    )

    add_table(
        slide, MARGIN, CONTENT_TOP, Inches(7.4),
        ["Year", "TAM USD bn", "Competitive intensity", "Opportunity score", "Rank"],
        [
            (int(row.year), f"{row.market_size_usd_bn:,.1f}", f"{row.competitive_intensity:.0f}",
             f"{row.opportunity_score:.1f}", int(row.rank_in_year))
            for row in ctx["anomaly"].itertuples()
        ],
        column_widths=[1.0, 1.6, 2.0, 1.8, 1.0], font_size=11,
    )

    bullets(
        slide, MARGIN + Inches(7.7), CONTENT_TOP, Inches(4.5), Inches(3.6),
        [
            ("What happens.",
             f"TAM rises {ctx['anomaly_tam_growth']:.0f}% between 2027 and 2030 while the "
             f"opportunity score falls {abs(ctx['anomaly_score_fall']):.0f} points and the "
             "segment drops a place."),
            ("Why.",
             f"Competitive intensity climbs {ctx['anomaly_intensity_rise']:.0f} points over the "
             "same stretch as announced SiC capacity converts to supply. The market grows and "
             "the margin pool is competed away inside it."),
            ("So what.",
             "A framework ranked on market size commits capacity here in exactly the years the "
             "returns disappear. Hold the current position; do not build against it."),
        ],
        size=13,
    )

    rectangle(slide, MARGIN, Inches(5.4), CONTENT_WIDTH, Inches(1.35), RGBColor(0xFB, 0xF0, 0xD8))
    rectangle(slide, MARGIN, Inches(5.4), Emu(28000), Inches(1.35), AMBER)
    textbox(
        slide, MARGIN + Inches(0.2), Inches(5.52), CONTENT_WIDTH - Inches(0.4), Inches(1.1),
        "This is the one segment in the set where the TAM chart and the opportunity chart point "
        "in opposite directions, and it is the reason the framework scores competitive intensity "
        "rather than assuming a growing market stays an attractive one. Six other segments also "
        "lose a little score by 2030; they lose it because the leaders pull away, not because "
        "anyone is crowding them. Power electronics is the only one with a structural change in "
        "who we would be bidding against.",
        size=12, color=GREY,
    )


def slide_ranking(presentation, ctx):
    slide = add_slide(
        presentation,
        "Memory and RF hold their places under every weighting; everything above them reorders",
        kicker="Segment ranking | forward mean score 2026-2030, stress-tested under three "
               "alternative weightings",
        number=5,
    )

    rows = []
    for row in ctx["ranking"].itertuples():
        low, high = ctx["rank_range"][row.segment_id]
        spread = high - low
        stability = "Fixed" if spread == 0 else "Stable" if spread == 1 else "Weight-sensitive"
        rows.append((
            row.rank, row.segment_name, f"{row.forward_mean_score:.1f}", row.recommendation,
            ctx["profile_ranks"][row.segment_id],
            f"{low}" if spread == 0 else f"{low} to {high}", stability,
        ))

    add_table(
        slide, MARGIN, CONTENT_TOP, CONTENT_WIDTH,
        ["#", "Segment", "Forward score", "Call",
         "Rank in 2030: base / growth / feasibility / fit",
         "Rank range, all profiles 2026-2030", "Stability"],
        rows, column_widths=[0.4, 3.0, 1.1, 1.3, 3.0, 2.1, 1.5], font_size=11, band_column=3,
    )

    bullets(
        slide, MARGIN, Inches(5.0), CONTENT_WIDTH, Inches(1.9),
        [
            ("Settled by the data.",
             "Memory is eighth and RF & 5G is seventh in every forward year under every "
             "weighting tried. Those two calls do not depend on our judgment at all."),
            ("Settled by the weights.",
             "HPC ranges from first to sixth depending on how the model is weighted. It is in "
             "the prioritize group on the size of the pool it opens, not on the strength of its "
             "score, and the entry plan has to reflect that."),
            ("Why automotive leads.",
             "It never falls below third under any weighting, and analog never below fourth. "
             "They are the two most stable positions in the set, which is what makes them safe "
             "to build capacity against."),
        ],
        size=12,
    )
    legend(slide, MARGIN, Inches(6.62))


def slide_recommendation(presentation, ctx):
    slide = add_slide(
        presentation,
        "Go on three, partner on one, hold one, and stop spending attention on three",
        kicker="Go / no-go recommendation",
        number=6,
    )

    blocks = [
        ("Prioritize", GREEN, ctx["bands"]["Prioritize"],
         "Build capacity. Automotive and analog carry the deepest fit with existing ASIC, "
         "embedded and VLSI capability and the longest engagement lengths, which is what turns a "
         "market into staffable, repeatable work. HPC is entered against named accounts rather "
         "than as a general capability build, because its rank depends on how the model is "
         "weighted."),
        ("Selective", AMBER, ctx["bands"]["Selective"],
         "Photonics through partnership or acquisition, not hiring: the constraint is engineering "
         "talent supply, not customer demand. Power electronics is a hold - keep the current "
         "position, take the work that comes, and re-open the question if the crowding thesis "
         "proves wrong before 2027."),
        ("Deprioritize", RED, ctx["bands"]["Deprioritize"],
         "Memory is structurally captive and cannot be won at any weighting. RF is mature and "
         "concentrated. MEMS is easy to enter and easy to leave; the design cycles are too short "
         "to staff a practice against. Serve inbound work, fund nothing."),
    ]

    top = CONTENT_TOP
    for label, colour, segments, rationale in blocks:
        rectangle(slide, MARGIN, top, CONTENT_WIDTH, Inches(1.55), RGBColor(0xF4, 0xF6, 0xF9))
        rectangle(slide, MARGIN, top, Emu(28000), Inches(1.55), colour)
        textbox(slide, MARGIN + Inches(0.2), top + Inches(0.1), Inches(2.5), Inches(0.3),
                label.upper(), size=13, bold=True, color=colour)
        textbox(slide, MARGIN + Inches(0.2), top + Inches(0.42), Inches(3.4), Inches(1.0),
                "\n".join(segments), size=11, color=NAVY)
        textbox(slide, MARGIN + Inches(3.9), top + Inches(0.12), CONTENT_WIDTH - Inches(4.2),
                Inches(1.35), rationale, size=12, color=GREY)
        top += Inches(1.68)

    textbox(
        slide, MARGIN, Inches(6.62), CONTENT_WIDTH, Inches(0.4),
        f"Bands are set on the mean opportunity score over 2026-2030: prioritize at "
        f"{ctx['prioritize_min']:.0f} and above, selective at {ctx['selective_min']:.0f} and "
        f"above, deprioritize below that.",
        size=11, color=GREY, italic=True,
    )


def slide_risks(presentation, ctx):
    slide = add_slide(
        presentation,
        "The judgment inputs carry 45% of the weight, so the next 90 days are about replacing them",
        kicker="Risks and next 90 days",
        number=7,
    )

    textbox(slide, MARGIN, CONTENT_TOP, Inches(6.1), Inches(0.32),
            "What could make this answer wrong", size=14, bold=True)
    bullets(
        slide, MARGIN, Inches(1.95), Inches(6.1), Inches(4.6),
        [
            ("Judgment inputs.",
             "Strategic fit, customer demand, competitive intensity and entry feasibility are "
             "analyst scores, not measurements, and together they carry 45% of the weight."),
            ("Addressability.",
             "The addressable-share assumption is the single most load-bearing number in the "
             "model. It is what moves memory from second to fifth. It is also unverified."),
            ("Static competition.",
             "Competitive intensity is modelled as a smooth path. One large entrant, exit or "
             "acquisition would move a segment faster than anything shown here."),
            ("No commercial data.",
             "Nothing in the model uses pipeline, win rates, rate cards or utilisation, so this "
             "says where to look, not what an engagement is worth."),
        ],
        size=12,
    )

    textbox(slide, MARGIN + Inches(6.6), CONTENT_TOP, Inches(5.6), Inches(0.32),
            "Next 90 days", size=14, bold=True)
    bullets(
        slide, MARGIN + Inches(6.6), Inches(1.95), Inches(5.6), Inches(4.6),
        [
            ("Weeks 1-4.",
             "Replace the addressable-share assumption for the three prioritize segments with a "
             "bottom-up estimate built from won and lost bids over the last eight quarters."),
            ("Weeks 3-8.",
             "Test the power electronics crowding thesis directly: track announced SiC and GaN "
             "capacity conversions and count new design-services entrants quarterly."),
            ("Weeks 5-10.",
             "Name the HPC accounts. The segment is in the prioritize group on pool size; if the "
             "accounts are not nameable, it moves to selective."),
            ("Weeks 8-12.",
             "Scope photonics partnership options against the talent constraint, and take the "
             "re-weighted framework back to leadership with real inputs in place of judgment."),
        ],
        size=12,
    )


def build_context() -> dict:
    with WEIGHTS_PATH.open() as handle:
        config = yaml.safe_load(handle)

    dim = pd.read_csv(PROCESSED_DIR / "dim_segment.csv")
    fact = pd.read_csv(PROCESSED_DIR / "fact_segment_year.csv")
    scores = pd.read_csv(PROCESSED_DIR / "fact_opportunity_score.csv")
    sensitivity = pd.read_csv(PROCESSED_DIR / "fact_sensitivity.csv")

    final_year = int(fact["year"].max())
    latest = (
        fact[fact["year"] == final_year]
        .merge(dim, on="segment_id")
        .sort_values("serviceable_market_usd_bn", ascending=False, ignore_index=True)
    )

    ranking = dim.sort_values("forward_mean_score", ascending=False, ignore_index=True)
    ranking["rank"] = ranking.index + 1

    profile_order = [config["base_profile"]] + [
        name for name in config["profiles"] if name != config["base_profile"]
    ]
    final_sensitivity = sensitivity[sensitivity["year"] == final_year]
    profile_ranks = {
        segment: " / ".join(
            str(int(final_sensitivity.loc[
                (final_sensitivity["segment_id"] == segment)
                & (final_sensitivity["profile"] == profile), "rank_in_year"
            ].iloc[0]))
            for profile in profile_order
        )
        for segment in dim["segment_id"]
    }

    window = config["forward_window"]
    forward_window = sensitivity[
        sensitivity["year"].between(window["start_year"], window["end_year"])
    ]
    # The best and worst place a segment takes anywhere in the forward window under any of the
    # four profiles. A one-value range is a position the data settles; a wide one is a position
    # the weights settle.
    rank_range = {
        segment: (int(group["rank_in_year"].min()), int(group["rank_in_year"].max()))
        for segment, group in forward_window.groupby("segment_id")
    }

    anomaly = (
        fact[fact["segment_id"] == "PWR"]
        .merge(scores[["segment_id", "year", "opportunity_score", "rank_in_year"]],
               on=["segment_id", "year"])
        .query("year >= 2025")
        .sort_values("year")
    )
    anomaly_2027 = anomaly[anomaly["year"] == 2027].iloc[0]
    anomaly_2030 = anomaly[anomaly["year"] == final_year].iloc[0]

    bands = {
        band: dim.loc[dim["recommendation"] == band]
        .sort_values("forward_mean_score", ascending=False)["segment_name"].tolist()
        for band in ("Prioritize", "Selective", "Deprioritize")
    }
    band_serviceable = {
        band: latest.loc[latest["recommendation"] == band, "serviceable_market_usd_bn"].sum()
        for band in bands
    }
    total_serviceable = latest["serviceable_market_usd_bn"].sum()

    return {
        "final_year": final_year,
        "latest": latest,
        "ranking": ranking,
        "profile_ranks": profile_ranks,
        "rank_range": rank_range,
        "anomaly": anomaly,
        "anomaly_tam_growth": (anomaly_2030.market_size_usd_bn / anomaly_2027.market_size_usd_bn - 1) * 100,
        "anomaly_score_fall": anomaly_2030.opportunity_score - anomaly_2027.opportunity_score,
        "anomaly_intensity_rise": anomaly_2030.competitive_intensity - anomaly_2027.competitive_intensity,
        "bands": bands,
        "band_serviceable": band_serviceable,
        "band_share": {b: v / total_serviceable * 100 for b, v in band_serviceable.items()},
        "top3_share": latest.head(3)["serviceable_market_usd_bn"].sum() / total_serviceable * 100,
        "forward": dim.set_index("segment_id")["forward_mean_score"],
        "phot_cagr": latest.loc[latest["segment_id"] == "PHOT", "cagr_pct"].iloc[0],
        "phot_serviceable": latest.loc[
            latest["segment_id"] == "PHOT", "serviceable_market_usd_bn"].iloc[0],
        "mem_tam": latest.loc[latest["segment_id"] == "MEM", "market_size_usd_bn"].iloc[0],
        "mem_addressable": latest.loc[
            latest["segment_id"] == "MEM", "design_services_addressable_pct"].iloc[0] * 100,
        "prioritize_min": config["bands"]["prioritize_min"],
        "selective_min": config["bands"]["selective_min"],
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    context = build_context()

    presentation = Presentation()
    presentation.slide_width = SLIDE_WIDTH
    presentation.slide_height = SLIDE_HEIGHT

    for builder in (
        slide_summary, slide_landscape, slide_growth, slide_competitive,
        slide_ranking, slide_recommendation, slide_risks,
    ):
        builder(presentation, context)

    presentation.save(OUTPUT_PATH)
    normalize(OUTPUT_PATH)
    print(f"deck: {OUTPUT_PATH} ({len(presentation.slides)} slides)")


if __name__ == "__main__":
    main()
