# M20 scheduled-macro-window mid-alpha atlas — VALIDATE

Family `sched_window_v1` (registered 2026-07-22). STAGE-1 conditional MID-ALPHA SCREEN — mid-to-mid, no fills, no replay, NOT economics. Continuation hypothesis every cell: `signed_ret_bps = sign(reaction) x (exit_mid/entry_mid - 1) x 1e4`. Day-clustered CR0 95% CI (cluster = ET session), pooled across the 5 names.

generated: 2026-07-22T04:28:03.477828+00:00    audit rows (validate): 1640
cells computed: 2    SCREEN-PASS: 0  (VALIDATE: listed TRAIN passers only; confirm = same sign AND CI not entirely < 0)

## Cost floors (frozen; computed on TRAIN before any conditional mean)

| class            | symbol | median_spread_bps | floor_bps | n_spreads | class_floor_bps |
|------------------|--------|-------------------|-----------|-----------|-----------------|
| fomc_stmt        | NVDA   | 3.6618            | 4.9118    | 5531      | 4.6958          |
| fomc_stmt        | TSLA   | 3.4458            | 4.6958    | 5629      | 4.6958          |
| fomc_stmt        | AMD    | 2.8095            | 4.0595    | 5740      | 4.6958          |
| fomc_stmt        | MU     | 3.6597            | 4.9097    | 5324      | 4.6958          |
| fomc_stmt        | GOOGL  | 2.055             | 3.305     | 5298      | 4.6958          |
| fomc_minutes     | NVDA   | 2.6645            | 3.9145    | 5525      | 3.6152          |
| fomc_minutes     | TSLA   | 2.4179            | 3.6679    | 5653      | 3.6152          |
| fomc_minutes     | AMD    | 1.8596            | 3.1096    | 5677      | 3.6152          |
| fomc_minutes     | MU     | 2.3652            | 3.6152    | 5370      | 3.6152          |
| fomc_minutes     | GOOGL  | 1.6367            | 2.8867    | 5114      | 3.6152          |
| cluster_1000     | NVDA   | 2.7977            | 4.0477    | 51968     | 4.0477          |
| cluster_1000     | TSLA   | 2.9352            | 4.1852    | 53048     | 4.0477          |
| cluster_1000     | AMD    | 2.1087            | 3.3587    | 53428     | 4.0477          |
| cluster_1000     | MU     | 2.8864            | 4.1364    | 51794     | 4.0477          |
| cluster_1000     | GOOGL  | 1.6777            | 2.9277    | 48524     | 4.0477          |
| tsy_auction_1300 | NVDA   | 1.7704            | 3.0204    | 16286     | 3.0298          |
| tsy_auction_1300 | TSLA   | 2.0333            | 3.2833    | 16984     | 3.0298          |
| tsy_auction_1300 | AMD    | 1.7798            | 3.0298    | 17475     | 3.0298          |
| tsy_auction_1300 | MU     | 2.0208            | 3.2708    | 16057     | 3.0298          |
| tsy_auction_1300 | GOOGL  | 1.1361            | 2.3861    | 14895     | 3.0298          |
| pre_open_0830    | NVDA   | 4.1735            | 5.4235    | 37140     | 5.4235          |
| pre_open_0830    | TSLA   | 4.3434            | 5.5934    | 37771     | 5.4235          |
| pre_open_0830    | AMD    | 3.2067            | 4.4567    | 37844     | 5.4235          |
| pre_open_0830    | MU     | 4.3094            | 5.5594    | 36629     | 5.4235          |
| pre_open_0830    | GOOGL  | 2.5143            | 3.7643    | 35011     | 5.4235          |

## Atlas cells

| cell_id             | N  | n_sessions | mean_bps | ci_lo    | ci_hi   | floor_bps | bar_2x_floor | screen_pass | underpowered | per_symbol_mean                   | validate_confirm | validate_underpowered |
|---------------------|----|------------|----------|----------|---------|-----------|--------------|-------------|--------------|-----------------------------------|------------------|-----------------------|
| cluster_1000|C2|h30 | 43 | 15         | -3.835   | -39.1312 | 31.4611 | 4.0477    | 8.0954       | false       | true         | AMD:28.125 GOOGL:-11.088 MU:-3... | false            | false                 |
| cluster_1000|C2|h60 | 43 | 15         | -7.4388  | -50.8829 | 36.0054 | 4.0477    | 8.0954       | false       | true         | AMD:22.335 GOOGL:-13.12 MU:-22... | false            | false                 |

## Drop reasons — event-level (per event x symbol)

| class            | status        | n |
|------------------|---------------|---|
| tsy_auction_1300 | zero_reaction | 1 |

## Drop reasons — horizon-level (per event x symbol x horizon)

(no horizon-level drops)

## C2 magnitude-gate membership (per class, entry-reached events)

| class            | n_entry_reached | n_in_c2 | n_excl_priors | n_excl_magnitude |
|------------------|-----------------|---------|---------------|------------------|
| cluster_1000     | 90              | 43      | 0             | 47               |
| fomc_minutes     | 10              | 4       | 0             | 6                |
| fomc_stmt        | 10              | 4       | 0             | 6                |
| pre_open_0830    | 65              | 42      | 0             | 23               |
| tsy_auction_1300 | 29              | 16      | 0             | 13               |
