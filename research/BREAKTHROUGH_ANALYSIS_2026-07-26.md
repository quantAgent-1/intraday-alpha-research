# Where the breakthrough is — a diagnosis of 22 families

Written 2026-07-26 against: HANDOFF (session 7 end-state), session-8 commits `93061a6..719b298`,
`research/ledger.jsonl` (133 rows, 22 registered families), `EXHAUSTION_MAP.md`,
`HYPOTHESES_FABLE_MAX.md` (rounds 1–2), and the **uncommitted, unledgered**
`research/experiments/R2A-prong0/` result that landed 2026-07-24.

All numbers below are measured on **owned data** during the writing of this memo. Probe
scripts are disposable; the three that matter are reproduced inline so they can be re-run.
No look was spent, no family was touched, no economics claim is made about any family.

---

## 0. The claim

**The wall is not an idea wall. It is a denominator wall.**

Every family in this program dies against one of two inequalities:

```
PROMOTION:  alpha_gross  >=  2 x c          c = round-trip cost of the instrument chosen
DETECTION:  alpha_gross  >=  2 x sigma/sqrt(n)   sigma = noise of the portfolio shape chosen
```

Twenty-two registered families have varied **alpha**. Not one has varied **c** or **sigma**.
Both are engineering variables this program fully controls, and both are measured below to be
**3x–40x improvable on data already on disk, at $0.**

That is why the recent sequence reads the way it does — "the effect is real, the taker floor is
2x" (M27), "point-strong near-miss, CI spans zero" (M24, M22, M16-A, R2-A). Those are not
statements about the market. They are statements about a numerator being tested against
denominators nobody has optimised.

---

## 1. Evidence: the cost floor is not a constant, it is a 50x surface

Median **quoted spread in bps**, measured from owned `data/raw/bbo1s`, 12 monthly files
2025-06 → 2026-05, sampled in three 60-second windows:

| name | 09:35 | 12:00 | 15:40 | px |
|---|---|---|---|---|
| NVDA | **0.8** | 0.6 | **0.6** | 185 |
| GOOGL | 1.6 | 0.7 | 0.6 | 295 |
| TSLA | 2.8 | 1.3 | 1.0 | 415 |
| AMD | 5.4 | 2.4 | 1.5 | 211 |
| MU | 6.9 | 3.4 | 2.4 | 243 |
| MRVL | 8.2 | 3.2 | 2.2 | 83 |
| LRCX | 9.5 | 4.6 | 2.0 | 154 |
| TXN | 12.1 | 4.3 | 1.9 | 194 |
| AMAT | 14.0 | 6.3 | 3.7 | 231 |
| KLAC | **30.0** | 11.9 | 7.5 | 1161 |

A taker round trip costs one full quoted spread (half per leg). So the round-trip floor ranges
from **~0.7 bps (NVDA, 09:35 in / 15:40 out)** to **~19 bps (KLAC, same clock)** — a **27x
range across names**, plus a further **2–4x within the day** on the illiquid tier. This
independently reproduces M27's frozen floors (pooled RT 16.0 bps, KLAC alone 38.5) from a
different data path, so the surface is trustworthy.

Now overlay the kills:

- **M27** measured a genuine `+7 to +11 bps` mid-alpha and was killed by a 16-bps pooled floor.
  That same alpha at NVDA/GOOGL's clock costs **0.7–1.1 bps** — it clears the house 2x
  promotion rule by **4–6x**.
- **M27's panel was chosen by an "exogenous bottom-ADV rule"** — i.e. the design deliberately
  selected the most expensive names on the surface, then died of the expense.
- The 3x semis ETF **SOXL** (owned `bars1m`, median $183.59 in 2026-07) has a one-tick floor of
  **0.545 bps**; TQQQ at $75.05 is 1.33 bps. A semis-index expression of a semis-wide signal
  prices at roughly **1 bps round trip, with 3x the move**.

The known counter-argument is real and must be stated: M24's liquidity mirror (broad-28 +15.35
vs champion-5 −19.63) says the *effect* is larger where liquidity is thinner. But the **effect
ratio is ~2–3x and the cost ratio is 20–40x.** The program has never once ranked candidates by
alpha-per-unit-cost. It measures alpha on a fixed panel, then applies cost afterwards as a kill
filter. That ordering manufactures the "real but 2x under the floor" verdict.

---

## 2. Evidence: the noise is 3.2x bigger than it needs to be

Measured on owned `data/raw/sip/bars1d`, **R2-A's exact 10 names and exact 603-session window**,
signal proxy = prior-day close-to-close return (a real, cross-sectionally correlated signal of
the kind every family here has used), **all designs normalised to gross exposure = 1.0** so that
bps of noise and bps of cost are directly comparable:

| design (gross = 1.0) | daily sd | SE over 603 sess | min. detectable effect @ t=2 |
|---|---|---|---|
| **1. directional pooled** — *the shape of every family run to date* | 144.3 | 5.88 | **11.75 bps** |
| 2. dollar-neutral cross-sectional | 85.4 | 3.48 | 6.96 bps |
| 3. **directional, net exposure hedged** | 45.1 | **1.84** | **3.68 bps** |

The house design carries **0.58 units of net market exposure per unit of gross**. That market
bet supplies essentially all of the variance and, in expectation, none of the mean. Hedging it
away with a single index leg cuts the standard error **3.2x — statistically equivalent to 10x
more data** — for roughly 0.3–1 bps of added cost.

On the full 1,650-session sample the same three shapes give SE 3.66 / 2.20 / 1.04 (3.5x); on the
37-name lake already on disk, 2.52 / 2.66 / 1.02 (2.5x). The effect is structural, not a window
artifact.

**Q16 — "is there a variance-reduction framing that cuts the 20-bps noise rather than chasing the
small mean?" — has been OPEN-TESTABLE on the map since day one and has never been run.** It is
the cheapest unspent item in the entire research inventory and it is worth more than any signal
improvement this program has produced.

---

## 3. Evidence: the kills are mostly power failures

| family | point | implied se | t | data multiple needed for CI-lo > 0 |
|---|---|---|---|---|
| **R2-A** gate (b) top-quartile fade | +14.87 | 8.00 | 1.86 | **1.11x** |
| M24 open-fade t50 | +37.1 | 22.24 | 1.67 | 1.38x |
| M22 Cell A earnings-close | +3.70 | 2.39 | 1.55 | 1.60x |
| M16-A flow-book | +1.69 | 1.25 | 1.35 | 2.09x |
| M17-A XS momentum | — | — | 1.01 | 3.8x |
| M17-B sector momentum | — | — | 0.86 | 5.2x |

Six positive-mean results at t = 0.86–1.86. None reached 1.96. All are closed. **The median
"kill" in this program is ~1.5x the sample size away from a pass.**

Run the protocol's own arithmetic forward: with SE ≈ 8 bps and a true effect of 5–15 bps, a
one-look / CI-lo > 0 / no-iteration rule passes a *genuinely real* edge with probability
**0.15–0.35**. Over 22 families, that filter is expected to have discarded several real effects
and written them into `EXHAUSTION_MAP.md` as EXHAUSTED. **The map is being populated with false
negatives, which is exactly what "hitting a wall" feels like from the inside.**

The discipline is not wrong — it is what has kept this project honest, and the alternative
(loosening the bar) invites the false positives the program was built to avoid. The defect is
narrower and fixable: **the protocol has a bar but no power requirement.** Families are
registered without anyone computing, in advance, whether the design *could* detect the effect it
is looking for. Underpowered looks are then spent, and their spanning CIs are recorded as
exhaustion.

### 3.1 The live case: R2-A

Result on disk 2026-07-24, **uncommitted and unledgered — the adjudication has not yet been
made**, so this memo lands before it rather than after:

- gate (a) residualised rho = +0.0067 [−0.027, +0.040] — a clean, adequately powered **null**.
- gate (b) top-quartile signed fade = **+14.87 bps [−1.17, +30.19]**, n=1,094 — point estimate
  **2.5x the pre-declared +6 bar**, CI-lo missing zero by 1.17 bps.
- **8 of 10 names positive** (one-sided binomial p = 0.055); MRVL +23.6, TXN +22.3, AMAT +20.2,
  NVDA +17.1, LRCX +15.7, MU +14.3, AMD +31.5; only TSLA (−9.4) and KLAC (−1.7) negative.
- Horizon table: **+3.56 bps at 10:00 → +4.66 at 11:00 → +14.87 at 15:45.**

Mechanically that is `label = KILL`, and the pre-declaration is authoritative. But the
pre-declaration also provided a **PARK-UNDERPOWERED** outcome precisely for this shape, and the
honest read of gate (b) is underpowered-positive, not dead. Gate (a) is a real null and should
be recorded as one: the *linear, gap-residualised* channel is empty. Gate (b) is a different
claim (non-linear, extreme-quartile) and it is 1.11x of data from resolution.

---

## 4. Evidence: the horizon is free and you are not taking it

R2-A's own horizon table shows the effect growing **~4x from 10:00 to 15:45** while cost stays
fixed. At the same time the cost table in §1 shows entry at 09:35 is the **most expensive minute
of the day** (KLAC 30.0) and 15:40 the **cheapest** (7.5).

Every recent family enters at the open and exits early. The arithmetic says the opposite:
**enter at the opening cross (a single print — zero spread by construction, the K4 exception
already identified in the round-2 memo) and exit at 15:40–15:45.** That is simultaneously the
largest measured effect and the lowest measured cost available in this dataset. R2-A is the one
design in the program whose *shape* was already right.

---

## 5. What to do — three moves, ranked, all $0

### MOVE 1 — Re-price the graveyard against the cost surface (0–2 days, $0, no look spent)

Take every family whose **mid-alpha was measured real and killed only on cost** — M27
(+7–11 bps gross), M24 (+37.1 t50), R2-A (+14.87) — and recompute the economics across the
`name x clock x instrument` grid using the measured surface from §1, in three instruments: the
single name, SMH/SOXX (1x), SOXL (3x).

This spends no new look because it makes no new economic claim: it re-prices already-published
measurements under a corrected cost model, the same class of action as the COST_MODEL v1
adoption. It answers the one question that decides whether this program has a future on owned
data: **is there any (name x clock x instrument) cell where an already-measured alpha clears 2x
its actual floor?** A clean "no" is itself the most valuable negative result available — it
would be the first time cost-exhaustion is established as a fact rather than assumed one family
at a time.

### MOVE 2 — Fix the portfolio shape before registering anything else (~1 week, $0)

Adopt a standing registration rule with the same force as the ADIA reporting standard:

> **No family may be registered carrying a net factor exposure it did not intend, and no family
> may be registered before its minimum detectable effect is computed and shown to be below the
> hypothesised effect.**

Operationally: every design acquires a second leg (short SMH or QQQ against the net), the
estimator becomes the residual, and the registration document must state MDE alongside the bar.
Worth **3.2x on the SE** (§2) — more than any signal improvement in the project's history — and
it closes Q16 at the same time.

Note the honest fork: hedging removes common-factor *alpha* along with common-factor *noise*. If
a signal's alpha is a factor bet, the hedged version reads zero. That is not a loss — the
decomposition tells you which component carries the alpha, and the common branch routes straight
to the cheap ETF/LETF expression of §1. **There is no losing branch; there are two different
answers, each cheaper to trade than what is being traded now.**

### MOVE 3 — Widen the panel with free data (1–2 days background, $0)

The capability is already proven in this repo: `data/external/m17_daily_bars.parquet` holds
**659 symbols x 7 years, 1.16M rows**, built from free Alpaca history for M17. Every recent
family used 5–10 names.

Going from 10 to 40–100 liquid names multiplies name-days 4–10x and — more importantly — is what
makes the cross-sectional design of Move 2 possible at all. The R2-A backfill (3,020 name-days
of *trades* in 3.7 h) shows the pull machinery works; bar pulls are ~100x cheaper than trades.
The 5-name panels are a self-imposed constraint inherited from Databento pricing, and they no
longer bind for anything bar-anchored or daily-anchored.

### THEN — the combination, as one forward-judged registration

The multi-signal doctrine says breadth is binding and the champion's streams (rho 0.83–0.98)
give effective breadth ~1. But **M24 measured rho = −0.073 between the open axis and the
champion** — a genuinely independent axis, and the finding was recorded as durable.

There are now 4–6 weak, near-independent, positive-mean streams sitting in the graveyard. Five
streams at t≈1.5 with rho≈0 combine to **t ≈ 3.4**. A single registration of the *portfolio* of
survivors, judged on forward data, relitigates none of the individual looks and dissolves the
multiple-testing objection by construction. This is the shape the program's own doctrine has
been pointing at since session 7 — it was blocked because breadth was being hunted as "one more
family" instead of assembled from what was already measured.

---

## 6. What I would not do

- **Not more ideation.** Round 2's full EMPTY-cell re-scan yielded exactly one candidate. Round 3
  yields less. The idea funnel has never been the constraint — 22 families is a lot of ideas.
- **Not more data purchases.** Everything above runs on owned or free data. Databento credits
  (~$2) stay untouched.
- **Not loosening the promotion bar.** The fix is more power, not a lower bar. Moves 1–3 raise
  power 3–10x while leaving the bar exactly where it is.
- **Nothing that touches the close auction.** All three moves live at the open and midday.

---

## 7. Risks and counter-arguments, stated plainly

1. **Selection bias.** Six t≈1.5 results out of 22 families is also what a null world with
   publication pressure looks like. The distinguishing evidence is sign-consistency across
   independent partitions (R2-A 8/10 names; M20 all 5 names, all 6 subtypes, 6–7/7 years;
   M16-A positive every LETF-era year) — a different signature from noise, but not proof.
   **Q17 (family-wise deflated-Sharpe accounting) has never been run and should be run as part
   of the combination registration, in both directions** — deflation *and* aggregation.
2. **The liquidity trap may be real.** If the effects genuinely live only where the spread eats
   them, Move 1 returns "no cell clears 2x". That is a decisive, publishable negative and it
   costs two days.
3. **Capital.** Hedged and cross-sectional designs need 2+ legs. Comfortable at the $10k research
   book, tight at the $1k small-account lens. The single-leg SOXL expression is the small-book
   version and is the only one that also multiplies the outcome by 3.
4. **Economic scale, said plainly.** At $10k and +5 bps/event, one event per day is ~$1,250/yr;
   at $1k it is ~$150/yr. Even a full success is marginal at current book size unless the edge
   is 20+ bps or fires several times a day. **The instrument axis is the only lever available
   that multiplies the outcome without requiring new alpha** — which is a second, independent
   reason to put it on the critical path.

---

## 8. The one-paragraph version

You have spent 22 families searching for a bigger numerator while holding two denominators
fixed at their worst available values: you tested cheap signals in the most expensive names on
the surface (a 27x cost range you never measured until today), in a portfolio shape that carries
0.58 units of unwanted market exposure per unit of gross (a 3.2x noise penalty), on 5–10-name
panels (while a 659-symbol free lake sits in `data/external/`). Six of your kills are
positive-mean results a median 1.5x of data short of significance, and they are recorded on the
map as exhausted. **Before generating one more hypothesis, re-price the ones you already
measured against the real cost surface, hedge the exposure you never wanted, and widen the panel
with data that is already free. That is a 3–10x improvement in both inequalities, it costs
approximately zero dollars and about a week, and it is the only move on the board that changes
the arithmetic instead of the ideas.**

---

### Reproduction

The three probes behind §1 and §2 (disposable, no repo dependency):

- **spread surface (§1)** — read `data/raw/bbo1s/<NAME>/*.parquet` for months >= 2025-06, keep
  `bid>0 & ask>bid`, convert `ts` to ET, take the median of `(ask-bid)/mid*1e4` inside the
  60 s windows starting 09:35 / 12:00 / 15:40, then the median across months.
- **design shapes (§2)** — from `data/raw/sip/bars1d`, build open->close returns in bps and the
  prior-day close-to-close signal; form three weight matrices each normalised to
  `sum|w| = 1`: `w1 = -sign(s)`, `w2 = -(s - rowmean(s))`, and `p3 = p1 - net1 * basket`;
  report `sd(p)` and `sd(p)/sqrt(T)`.
- **near-miss table (§3)** — `se = (hi - lo) / (2*1.96)`; `multiple = (1.96/t)^2`. CIs quoted
  verbatim from each family's report/ledger row.
