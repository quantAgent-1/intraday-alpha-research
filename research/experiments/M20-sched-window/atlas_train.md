# M20 scheduled-macro-window mid-alpha atlas — TRAIN

Family `sched_window_v1` (registered 2026-07-22). STAGE-1 conditional MID-ALPHA SCREEN — mid-to-mid, no fills, no replay, NOT economics. Continuation hypothesis every cell: `signed_ret_bps = sign(reaction) x (exit_mid/entry_mid - 1) x 1e4`. Day-clustered CR0 95% CI (cluster = ET session), pooled across the 5 names.

generated: 2026-07-22T04:22:20.343573+00:00    audit rows (train): 40080
cells computed: 40    SCREEN-PASS: 2  (TRAIN bar: mean >= 2x class floor AND ci_lo > 0 AND N >= 150 AND sessions >= 40)

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

| cell_id                    | N    | n_sessions | mean_bps | ci_lo     | ci_hi   | floor_bps | bar_2x_floor | screen_pass | underpowered | per_symbol_mean                   |
|----------------------------|------|------------|----------|-----------|---------|-----------|--------------|-------------|--------------|-----------------------------------|
| fomc_stmt|C1|h30           | 234  | 48         | -13.473  | -34.786   | 7.84    | 4.6958    | 9.3916       | false       | false        | AMD:-17.734 GOOGL:-11.639 MU:-... |
| fomc_stmt|C1|h60           | 234  | 48         | -11.0474 | -45.9785  | 23.8836 | 4.6958    | 9.3916       | false       | false        | AMD:-6.472 GOOGL:-16.233 MU:-1... |
| fomc_stmt|C1|h120          | 234  | 48         | 1.0244   | -38.7953  | 40.8441 | 4.6958    | 9.3916       | false       | false        | AMD:13.087 GOOGL:-6.853 MU:-2.... |
| fomc_stmt|C1|to1545        | 234  | 48         | 1.0244   | -38.7953  | 40.8441 | 4.6958    | 9.3916       | false       | false        | AMD:13.087 GOOGL:-6.853 MU:-2.... |
| fomc_stmt|C2|h30           | 96   | 30         | -15.5563 | -57.3635  | 26.2509 | 4.6958    | 9.3916       | false       | true         | AMD:-27.252 GOOGL:-9.29 MU:0.9... |
| fomc_stmt|C2|h60           | 96   | 30         | -51.0672 | -119.9269 | 17.7924 | 4.6958    | 9.3916       | false       | true         | AMD:-50.951 GOOGL:-28.613 MU:-... |
| fomc_stmt|C2|h120          | 96   | 30         | -27.3312 | -105.0275 | 50.3651 | 4.6958    | 9.3916       | false       | true         | AMD:0.238 GOOGL:-12.185 MU:10.... |
| fomc_stmt|C2|to1545        | 96   | 30         | -27.3312 | -105.0275 | 50.3651 | 4.6958    | 9.3916       | false       | true         | AMD:0.238 GOOGL:-12.185 MU:10.... |
| fomc_minutes|C1|h30        | 234  | 48         | 4.9143   | -7.533    | 17.3617 | 3.6152    | 7.2304       | false       | false        | AMD:7.153 GOOGL:-4.187 MU:22.0... |
| fomc_minutes|C1|h60        | 235  | 48         | 5.6406   | -9.6904   | 20.9716 | 3.6152    | 7.2304       | false       | false        | AMD:8.418 GOOGL:-1.078 MU:26.6... |
| fomc_minutes|C1|h120       | 234  | 48         | -1.8134  | -20.8819  | 17.255  | 3.6152    | 7.2304       | false       | false        | AMD:-8.488 GOOGL:0.42 MU:15.05... |
| fomc_minutes|C1|to1545     | 234  | 48         | -1.8134  | -20.8819  | 17.255  | 3.6152    | 7.2304       | false       | false        | AMD:-8.488 GOOGL:0.42 MU:15.05... |
| fomc_minutes|C2|h30        | 89   | 26         | 8.4879   | -17.8218  | 34.7976 | 3.6152    | 7.2304       | false       | true         | AMD:8.934 GOOGL:2.817 MU:27.03... |
| fomc_minutes|C2|h60        | 89   | 26         | 14.4265  | -14.9487  | 43.8018 | 3.6152    | 7.2304       | false       | true         | AMD:18.757 GOOGL:1.102 MU:33.9... |
| fomc_minutes|C2|h120       | 88   | 26         | 4.8505   | -27.6587  | 37.3598 | 3.6152    | 7.2304       | false       | true         | AMD:3.785 GOOGL:15.712 MU:25.0... |
| fomc_minutes|C2|to1545     | 88   | 26         | 4.8505   | -27.6587  | 37.3598 | 3.6152    | 7.2304       | false       | true         | AMD:3.785 GOOGL:15.712 MU:25.0... |
| cluster_1000|C1|h30        | 2193 | 410        | 5.3265   | -0.4339   | 11.0868 | 4.0477    | 8.0954       | false       | false        | AMD:3.332 GOOGL:1.749 MU:6.144... |
| cluster_1000|C1|h60        | 2197 | 410        | 7.3216   | -0.3708   | 15.0139 | 4.0477    | 8.0954       | false       | false        | AMD:10.551 GOOGL:3.411 MU:11.5... |
| cluster_1000|C1|h120       | 2191 | 410        | 5.1393   | -4.6778   | 14.9564 | 4.0477    | 8.0954       | false       | false        | AMD:6.205 GOOGL:3.857 MU:5.987... |
| cluster_1000|C1|to1545     | 2179 | 407        | 3.4149   | -9.0794   | 15.9091 | 4.0477    | 8.0954       | false       | false        | AMD:7.112 GOOGL:3.165 MU:7.741... |
| cluster_1000|C2|h30        | 1136 | 366        | 9.2675   | 0.1607    | 18.3743 | 4.0477    | 8.0954       | true        | false        | AMD:10.406 GOOGL:6.071 MU:4.64... |
| cluster_1000|C2|h60        | 1138 | 366        | 12.9287  | 0.6332    | 25.2243 | 4.0477    | 8.0954       | true        | false        | AMD:18.747 GOOGL:9.238 MU:7.32... |
| cluster_1000|C2|h120       | 1136 | 366        | 7.6321   | -8.0724   | 23.3365 | 4.0477    | 8.0954       | false       | false        | AMD:8.175 GOOGL:7.486 MU:0.063... |
| cluster_1000|C2|to1545     | 1135 | 364        | 3.8196   | -15.298   | 22.9373 | 4.0477    | 8.0954       | false       | false        | AMD:16.616 GOOGL:0.899 MU:-2.1... |
| tsy_auction_1300|C1|h30    | 720  | 148        | 3.5502   | -10.4976  | 17.5981 | 3.0298    | 6.0596       | false       | false        | AMD:7.419 GOOGL:0.988 MU:4.503... |
| tsy_auction_1300|C1|h60    | 719  | 148        | 10.4057  | -6.0879   | 26.8993 | 3.0298    | 6.0596       | false       | false        | AMD:14.446 GOOGL:4.89 MU:9.91 ... |
| tsy_auction_1300|C1|h120   | 718  | 148        | 10.8595  | -7.9936   | 29.7126 | 3.0298    | 6.0596       | false       | false        | AMD:14.907 GOOGL:5.808 MU:6.37... |
| tsy_auction_1300|C1|to1545 | 722  | 148        | 8.9121   | -14.08    | 31.9041 | 3.0298    | 6.0596       | false       | false        | AMD:12.731 GOOGL:1.178 MU:2.54... |
| tsy_auction_1300|C2|h30    | 334  | 120        | 11.3392  | -16.3384  | 39.0169 | 3.0298    | 6.0596       | false       | false        | AMD:17.505 GOOGL:3.902 MU:18.3... |
| tsy_auction_1300|C2|h60    | 334  | 120        | 24.3135  | -8.1305   | 56.7575 | 3.0298    | 6.0596       | false       | false        | AMD:37.129 GOOGL:9.942 MU:30.3... |
| tsy_auction_1300|C2|h120   | 331  | 120        | 25.5318  | -9.4826   | 60.5462 | 3.0298    | 6.0596       | false       | false        | AMD:37.98 GOOGL:12.974 MU:31.3... |
| tsy_auction_1300|C2|to1545 | 334  | 120        | 24.012   | -19.8369  | 67.861  | 3.0298    | 6.0596       | false       | false        | AMD:35.591 GOOGL:9.96 MU:25.07... |
| pre_open_0830|C1|h30       | 1471 | 301        | 1.2455   | -7.3217   | 9.8128  | 5.4235    | 10.847       | false       | false        | AMD:0.59 GOOGL:2.968 MU:2.17 N... |
| pre_open_0830|C1|h60       | 1472 | 301        | 0.8363   | -9.8486   | 11.5211 | 5.4235    | 10.847       | false       | false        | AMD:-0.976 GOOGL:-2.862 MU:4.9... |
| pre_open_0830|C1|h120      | 1469 | 301        | 2.2772   | -10.3034  | 14.8579 | 5.4235    | 10.847       | false       | false        | AMD:-4.983 GOOGL:-0.428 MU:1.7... |
| pre_open_0830|C1|to1545    | 1465 | 300        | 4.5201   | -11.4367  | 20.4768 | 5.4235    | 10.847       | false       | false        | AMD:6.343 GOOGL:8.513 MU:-2.58... |
| pre_open_0830|C2|h30       | 741  | 278        | 0.1783   | -13.0699  | 13.4264 | 5.4235    | 10.847       | false       | false        | AMD:-4.679 GOOGL:2.739 MU:9.23... |
| pre_open_0830|C2|h60       | 742  | 279        | -1.6547  | -17.8525  | 14.5431 | 5.4235    | 10.847       | false       | false        | AMD:-4.472 GOOGL:-8.037 MU:15.... |
| pre_open_0830|C2|h120      | 742  | 279        | -0.9227  | -19.7512  | 17.9059 | 5.4235    | 10.847       | false       | false        | AMD:-13.931 GOOGL:-0.708 MU:12... |
| pre_open_0830|C2|to1545    | 742  | 279        | 5.998    | -16.7194  | 28.7154 | 5.4235    | 10.847       | false       | false        | AMD:-1.265 GOOGL:10.336 MU:27.... |

## Drop reasons — event-level (per event x symbol)

| class            | status        | n  |
|------------------|---------------|----|
| cluster_1000     | stale_anchor  | 1  |
| cluster_1000     | stale_entry   | 1  |
| cluster_1000     | stale_react   | 3  |
| cluster_1000     | zero_reaction | 13 |
| fomc_minutes     | early_close   | 5  |
| fomc_minutes     | stale_anchor  | 5  |
| fomc_stmt        | stale_anchor  | 4  |
| fomc_stmt        | stale_entry   | 1  |
| fomc_stmt        | stale_react   | 1  |
| pre_open_0830    | stale_anchor  | 95 |
| pre_open_0830    | stale_react   | 2  |
| pre_open_0830    | zero_reaction | 1  |
| tsy_auction_1300 | stale_anchor  | 3  |
| tsy_auction_1300 | stale_entry   | 2  |
| tsy_auction_1300 | stale_react   | 3  |
| tsy_auction_1300 | zero_reaction | 10 |

## Drop reasons — horizon-level (per event x symbol x horizon)

| class            | status      | horizon | n  |
|------------------|-------------|---------|----|
| cluster_1000     | early_close | to1545  | 14 |
| cluster_1000     | stale_exit  | h120    | 6  |
| cluster_1000     | stale_exit  | h30     | 4  |
| cluster_1000     | stale_exit  | to1545  | 4  |
| fomc_minutes     | stale_exit  | h120    | 1  |
| fomc_minutes     | stale_exit  | h30     | 1  |
| fomc_minutes     | stale_exit  | to1545  | 1  |
| pre_open_0830    | early_close | to1545  | 5  |
| pre_open_0830    | stale_exit  | h120    | 3  |
| pre_open_0830    | stale_exit  | h30     | 1  |
| pre_open_0830    | stale_exit  | to1545  | 2  |
| tsy_auction_1300 | stale_exit  | h120    | 4  |
| tsy_auction_1300 | stale_exit  | h30     | 2  |
| tsy_auction_1300 | stale_exit  | h60     | 3  |

## C2 magnitude-gate membership (per class, entry-reached events)

| class            | n_entry_reached | n_in_c2 | n_excl_priors | n_excl_magnitude |
|------------------|-----------------|---------|---------------|------------------|
| cluster_1000     | 2197            | 1138    | 50            | 1009             |
| fomc_minutes     | 235             | 89      | 50            | 96               |
| fomc_stmt        | 234             | 96      | 49            | 89               |
| pre_open_0830    | 1472            | 742     | 50            | 680              |
| tsy_auction_1300 | 722             | 334     | 47            | 341              |
