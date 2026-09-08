# Where to commit design and engineering capacity, 2026-2030

**To:** Leadership, Cyient Semiconductors
**From:** Business Analysis
**Re:** End-market prioritization for design-services expansion

> Illustrative dataset constructed to be directionally consistent with publicly reported
> industry estimates. Figures are for methodology demonstration and are not market research.

---

## The question

We have finite design and engineering capacity. Across the semiconductor value chain, which
end-market segments should we expand into over the next three to five years, which should we
enter selectively or through partnership, and which should we stop spending attention on?

This memo answers with a prioritization framework and a go/no-go call per segment. It is not a
market forecast, and it should not be read as one.

## Recommendation

| Call | Segments | 2030 serviceable market | Share of pool |
|---|---|---|---|
| **Prioritize** | Automotive & ADAS silicon, Analog & mixed-signal, HPC / AI accelerator ASICs | USD 127bn | 72% |
| **Selective** | Silicon photonics / optical interconnect, Power electronics (SiC / GaN) | USD 21bn | 12% |
| **Deprioritize** | MEMS & sensors, RF & 5G front-end, Memory (DRAM / NAND) | USD 28bn | 16% |

Build capacity against automotive and analog. Enter HPC against named accounts rather than as a
general capability build. Partner into photonics rather than hiring into it. Hold the current
power electronics position and do not grow it. Serve inbound work in the bottom three and fund
nothing.

## Method

Eight end-market segments, modelled 2021-2030 on nine attributes. Seven of those attributes feed
a weighted additive score. Each is min-max normalized to 0-100 across the eight segments
**within each year**, so a score states a segment's standing relative to its peers that year,
not an absolute quantity. Competitive intensity is inverted before weighting, because a crowded
segment is a worse one.

| Factor | Weight |
|---|---|
| Serviceable market size | 20% |
| CAGR | 20% |
| Design-services addressability | 15% |
| Strategic fit | 15% |
| Customer demand | 10% |
| Competitive intensity (inverted) | 10% |
| Entry feasibility | 10% |

Two choices in that table do most of the work.

**We score on serviceable market, not TAM.** Serviceable market is TAM multiplied by the share of
a segment realistically reachable by an outsourced design-services provider. We cannot sell into
a market; we can only sell into the part of it that gets outsourced. Memory is the clearest case:
it is the second-largest market in the set at USD 271bn in 2030, and under 5% of it is
addressable, because the design work stays captive inside a handful of integrated device
manufacturers. On TAM it ranks second. On serviceable market it ranks fifth. A framework that
ranked on headline size would have pointed us at it.

**The band is set on a five-year average, not on one year.** Recommendations come from the mean
score over 2026-2030. A single year is too thin a basis for a multi-year capacity commitment, and
the final year of any projection is the least reliable one.

The weights live in one file, `config/weights.yaml`, read by both the Python scorer and the Excel
model, so the two cannot drift apart.

## Findings

**1. Size and attractiveness are different questions, and the gap between them is large.**
Ranking the 2030 market by TAM and by serviceable market produces materially different orders.
Memory falls from second to fifth. Automotive, analog and power electronics each rise a place.
Between 74% and 96% of every segment's TAM is out of our reach; the interesting variation is in
how much is left over.

**2. The prioritize group is concentrated.** Automotive, analog and HPC hold 72% of the 2030
serviceable pool and take the three highest forward scores (68.1, 67.2 and 64.1 out of 100).
Automotive and analog also carry the deepest fit with existing ASIC, embedded and VLSI
capability, which is what converts a market into staffable, repeatable work.

**3. Power electronics is a trap that only shows up when competition is scored.** TAM rises 56%
between 2027 and 2030. Over the same stretch the opportunity score falls from 55.9 to 40.0 and
the segment drops a rank, because competitive intensity climbs 39 points as announced SiC
capacity converts to supply. The market grows and the margin pool inside it is competed away.
Six other segments also lose a little score by 2030, but they lose it because the leaders pull
away, not because anyone is crowding them; power electronics is the only one with a structural
change in who we would be bidding against. Any framework ranked on market size commits capacity
here in precisely the years the returns disappear.

**4. Long engagements carry the pool.** Grouped by typical design-cycle length, the segments
running 14-19 month engagements hold 46% of the 2030 serviceable market at a mean score of 56,
against 9% and a mean score of 36 for those running under 14 months. Short-cycle work re-competes
constantly and is hard to staff a practice against. This is the argument for automotive and
analog stated in revenue-predictability terms rather than in market-size terms.

**5. The ranking is robust at the bottom and fragile in the middle.** Re-scored under three
alternative weightings - growth-weighted, feasibility-weighted and fit-weighted - memory stays
eighth and RF & 5G stays seventh in every forward year under every profile. Nothing else is
fixed. Automotive never falls below third and analog never below fourth, which is what makes them
safe to build against. HPC ranges from first to sixth. It is in the prioritize group on the size
of the pool it opens, not on the strength of its score, and it should be entered account by
account rather than as a capability build.

## Risks

The four judgment inputs - strategic fit, customer demand, competitive intensity and entry
feasibility - carry 45% of the weight between them and are analyst opinion, not measurement.

The addressable-share assumption is the single most load-bearing number in the model. It is what
moves memory from second to fifth, and it is unverified.

Competitive intensity is modelled as a smooth path. One large entrant, exit or acquisition would
move a segment faster than anything shown here, and the power electronics call in particular
depends on a crowding thesis that has not yet happened.

Nothing in the model uses pipeline, win rates, rate cards or utilisation. This says where to
look. It does not say what any particular engagement is worth.

## What data would change the answer

- **Won and lost bids by segment over the last eight quarters.** This replaces the
  addressable-share assumption with a bottom-up estimate. If addressability in memory turned out
  to be 10% rather than under 5%, memory moves back up the ranking and the framework's headline
  claim weakens.
- **Named accounts in HPC.** The HPC call rests on pool size. If the accounts cannot be named, it
  moves from prioritize to selective.
- **Quarterly counts of new design-services entrants in SiC and GaN.** If crowding does not
  materialise by 2027, power electronics moves from hold to build, and it moves quickly.
- **Rate cards and utilisation by practice.** Serviceable market is a revenue proxy, not a margin
  one. A large segment we serve at low utilisation may be worth less than a small one we do not.
- **Engineering talent supply in India by discipline.** Talent availability is modelled but not
  scored. It is the binding constraint on photonics, and it would convert that recommendation
  from a partnership question into a hiring plan if the supply were there.

## Next 90 days

| Weeks | Action |
|---|---|
| 1-4 | Rebuild the addressable-share estimate for the three prioritize segments from won and lost bid history. |
| 3-8 | Instrument the power electronics crowding thesis: track SiC and GaN capacity conversions and new entrants quarterly. |
| 5-10 | Name the HPC accounts, or move HPC to selective. |
| 8-12 | Scope photonics partnership options against the talent constraint, and bring the re-weighted framework back with measured inputs in place of judgment. |
