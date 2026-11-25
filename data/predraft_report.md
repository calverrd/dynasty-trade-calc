# Pre-draft prospect model v1: build + validation report

Pool: 1266 players (820 drafted, 1177 at the Combine), classes 2015-2026
pos
RB    384
TE    265
WR    617

Outcomes 2015-2024: 1061 players; source: {'sheet': 658, 'nflverse': 403}; safe rate 14.8%, upside rate 9.0%

College rows: 61895 player-seasons 2010-2025; columns ok: True
College match rate: 97.4% of pool, 97.4% of drafted players (by name only 55%, school-disambiguated 38%, most-recent-team 5%)
  WR: drafted matched 96.9% (n=393); 6+ game season found 93.9%
  RB: drafted matched 98.4% (n=245); 6+ game season found 95.5%
  TE: drafted matched 97.3% (n=182); 6+ game season found 90.7%

Wrote data/predraft_dataset.csv (1266 rows)

## WR · Drafted + Combine (n=517; safe 14%, upside 10%)
- **safe** anchors: log_pick 0.905 · log_rank 0.906 · both 0.906 → anchor = log_rank
  - +best_yard_share: AUC 0.903 (Δ -0.003 [-0.012, +0.004]) drop
  - +best_ypta: AUC 0.903 (Δ -0.003 [-0.010, +0.003]) drop
  - +final_ypta: AUC 0.903 (Δ -0.004 [-0.007, -0.001]) drop
  - +best_target_share: AUC 0.904 (Δ -0.003 [-0.010, +0.004]) drop
  - +breakout_age: AUC 0.904 (Δ -0.002 [-0.012, +0.008]) drop
  - +draft_age: AUC 0.907 (Δ +0.000 [-0.002, +0.002]) drop
  - +college_rush_capped: AUC 0.904 (Δ -0.003 [-0.006, +0.000]) drop
  - +wt: AUC 0.904 (Δ -0.002 [-0.005, +0.001]) drop
  - +speed_score: AUC 0.905 (Δ -0.001 [-0.006, +0.004]) drop
  - FINAL ['log_rank']: AUC 0.906; vs log_pick Δ +0.002 [-0.009, +0.011]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.078 (base 0.120)
  - calibration: 0-15%: 4% pred / 3% actual (n=392) · 15-35%: 23% pred / 31% actual (n=55) · 35-60%: 46% pred / 52% actual (n=33) · 60-80%: 69% pred / 68% actual (n=22) · 80-100%: 86% pred / 67% actual (n=15)
- **up** anchors: log_pick 0.896 · log_rank 0.905 · both 0.905 → anchor = log_rank
  - +best_yard_share: AUC 0.902 (Δ -0.003 [-0.007, -0.000]) drop
  - +best_ypta: AUC 0.901 (Δ -0.005 [-0.009, -0.001]) drop
  - +final_ypta: AUC 0.901 (Δ -0.004 [-0.009, -0.000]) drop
  - +best_target_share: AUC 0.902 (Δ -0.003 [-0.009, +0.001]) drop
  - +breakout_age: AUC 0.903 (Δ -0.003 [-0.008, +0.002]) drop
  - +draft_age: AUC 0.906 (Δ +0.000 [-0.002, +0.003]) drop
  - +college_rush_capped: AUC 0.902 (Δ -0.003 [-0.006, -0.000]) drop
  - +wt: AUC 0.906 (Δ +0.001 [-0.006, +0.009]) drop
  - +speed_score: AUC 0.904 (Δ -0.001 [-0.003, +0.001]) drop
  - FINAL ['log_rank']: AUC 0.905; vs log_pick Δ +0.010 [-0.001, +0.020]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.065 (base 0.087)
  - calibration: 0-15%: 3% pred / 3% actual (n=427) · 15-35%: 24% pred / 34% actual (n=47) · 35-60%: 46% pred / 46% actual (n=24) · 60-80%: 70% pred / 53% actual (n=19)

## WR · Rounds 1-3 (n=138; safe 44%, upside 32%)
- **safe** anchors: log_pick 0.662 · log_rank 0.709 · both 0.704 → anchor = log_rank
  - +best_yard_share: AUC 0.711 (Δ +0.003 [-0.031, +0.036]) drop
  - +best_ypta: AUC 0.711 (Δ +0.002 [-0.029, +0.032]) drop
  - +final_ypta: AUC 0.699 (Δ -0.010 [-0.029, +0.009]) drop
  - +best_target_share: AUC 0.709 (Δ +0.000 [-0.032, +0.034]) drop
  - +breakout_age: AUC 0.715 (Δ +0.006 [-0.036, +0.047]) drop
  - +draft_age: AUC 0.702 (Δ -0.007 [-0.020, +0.006]) drop
  - +college_rush_capped: AUC 0.699 (Δ -0.011 [-0.050, +0.026]) drop
  - +wt: AUC 0.690 (Δ -0.020 [-0.043, +0.001]) drop
  - +speed_score: AUC 0.705 (Δ -0.004 [-0.040, +0.033]) drop
  - FINAL ['log_rank']: AUC 0.709; vs log_pick Δ +0.046 [-0.005, +0.098]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.215 (base 0.247)
  - calibration: 15-35%: 27% pred / 25% actual (n=55) · 35-60%: 46% pred / 47% actual (n=51) · 60-80%: 70% pred / 78% actual (n=27) · 80-100%: 82% pred / 40% actual (n=5)
- **up** anchors: log_pick 0.603 · log_rank 0.681 · both 0.675 → anchor = log_rank
  - +best_yard_share: AUC 0.665 (Δ -0.016 [-0.044, +0.009]) drop
  - +best_ypta: AUC 0.664 (Δ -0.017 [-0.043, +0.007]) drop
  - +final_ypta: AUC 0.653 (Δ -0.028 [-0.046, -0.012]) drop
  - +best_target_share: AUC 0.663 (Δ -0.018 [-0.034, -0.005]) drop
  - +breakout_age: AUC 0.668 (Δ -0.013 [-0.031, +0.003]) drop
  - +draft_age: AUC 0.674 (Δ -0.007 [-0.019, +0.004]) drop
  - +college_rush_capped: AUC 0.661 (Δ -0.021 [-0.053, +0.006]) drop
  - +wt: AUC 0.662 (Δ -0.019 [-0.052, +0.009]) drop
  - +speed_score: AUC 0.682 (Δ +0.001 [-0.036, +0.035]) drop
  - FINAL ['log_rank']: AUC 0.681; vs log_pick Δ +0.078 [+0.016, +0.142]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.200 (base 0.217)
  - calibration: 0-15%: 14% pred / 0% actual (n=6) · 15-35%: 23% pred / 25% actual (n=83) · 35-60%: 45% pred / 46% actual (n=39) · 60-80%: 64% pred / 50% actual (n=10)

## RB · Drafted + Combine (n=331; safe 19%, upside 12%)
- **safe** anchors: log_pick 0.889 · log_rank 0.881 · both 0.887 → anchor = log_pick
  - +best_yard_share: AUC 0.890 (Δ +0.001 [-0.008, +0.011]) drop
  - +best_target_share: AUC 0.895 (Δ +0.006 [-0.006, +0.018]) drop
  - +best_rush_share: AUC 0.887 (Δ -0.002 [-0.006, +0.002]) drop
  - +best_scrim_pg: AUC 0.885 (Δ -0.004 [-0.015, +0.005]) drop
  - +draft_age: AUC 0.889 (Δ +0.001 [-0.004, +0.005]) drop
  - +wt: AUC 0.889 (Δ +0.000 [-0.005, +0.005]) drop
  - +speed_score: AUC 0.891 (Δ +0.002 [-0.007, +0.015]) drop
  - +breakout_age: AUC 0.891 (Δ +0.003 [-0.003, +0.010]) drop
  - FINAL ['log_pick']: AUC 0.889; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.008 [-0.011, +0.026]; Brier 0.091 (base 0.152)
  - calibration: 0-15%: 5% pred / 6% actual (n=226) · 15-35%: 22% pred / 23% actual (n=47) · 35-60%: 45% pred / 46% actual (n=24) · 60-80%: 71% pred / 50% actual (n=12) · 80-100%: 92% pred / 95% actual (n=22)
- **up** anchors: log_pick 0.854 · log_rank 0.857 · both 0.851 → anchor = log_rank
  - +best_yard_share: AUC 0.863 (Δ +0.007 [-0.006, +0.021]) drop
  - +best_target_share: AUC 0.865 (Δ +0.009 [-0.006, +0.024]) drop
  - +best_rush_share: AUC 0.856 (Δ -0.000 [-0.012, +0.011]) drop
  - +best_scrim_pg: AUC 0.855 (Δ -0.001 [-0.017, +0.012]) drop
  - +draft_age: AUC 0.859 (Δ +0.002 [-0.003, +0.009]) drop
  - +wt: AUC 0.853 (Δ -0.004 [-0.011, +0.002]) drop
  - +speed_score: AUC 0.853 (Δ -0.004 [-0.026, +0.018]) drop
  - +breakout_age: AUC 0.865 (Δ +0.009 [-0.003, +0.026]) drop
  - FINAL ['log_rank']: AUC 0.857; vs log_pick Δ +0.002 [-0.026, +0.030]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.072 (base 0.104)
  - calibration: 0-15%: 4% pred / 4% actual (n=258) · 15-35%: 23% pred / 17% actual (n=36) · 35-60%: 46% pred / 57% actual (n=23) · 60-80%: 71% pred / 64% actual (n=14)

## RB · Rounds 1-3 (n=66; safe 64%, upside 44%)
- **safe** anchors: log_pick 0.739 · log_rank 0.681 · both 0.698 → anchor = log_pick
  - +best_yard_share: AUC 0.752 (Δ +0.013 [-0.057, +0.087]) drop
  - +best_target_share: AUC 0.779 (Δ +0.039 [-0.045, +0.121]) drop
  - +best_rush_share: AUC 0.717 (Δ -0.022 [-0.054, +0.006]) drop
  - +best_scrim_pg: AUC 0.709 (Δ -0.030 [-0.064, -0.004]) drop
  - +draft_age: AUC 0.717 (Δ -0.022 [-0.055, +0.006]) drop
  - +wt: AUC 0.740 (Δ +0.001 [-0.028, +0.030]) drop
  - +speed_score: AUC 0.731 (Δ -0.008 [-0.041, +0.022]) drop
  - +breakout_age: AUC 0.774 (Δ +0.035 [-0.047, +0.122]) drop
  - FINAL ['log_pick']: AUC 0.739; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.059 [-0.063, +0.179]; Brier 0.194 (base 0.231)
  - calibration: 15-35%: 33% pred / 67% actual (n=3) · 35-60%: 47% pred / 46% actual (n=28) · 60-80%: 70% pred / 65% actual (n=20) · 80-100%: 92% pred / 93% actual (n=15)
- **up** anchors: log_pick 0.696 · log_rank 0.709 · both 0.701 → anchor = log_rank
  - +best_yard_share: AUC 0.752 (Δ +0.043 [-0.045, +0.124]) drop
  - +best_target_share: AUC 0.762 (Δ +0.053 [-0.030, +0.134]) drop
  - +best_rush_share: AUC 0.701 (Δ -0.008 [-0.031, +0.013]) drop
  - +best_scrim_pg: AUC 0.716 (Δ +0.007 [-0.015, +0.030]) drop
  - +draft_age: AUC 0.693 (Δ -0.015 [-0.039, +0.004]) drop
  - +wt: AUC 0.698 (Δ -0.011 [-0.042, +0.013]) drop
  - +speed_score: AUC 0.706 (Δ -0.003 [-0.053, +0.049]) drop
  - +breakout_age: AUC 0.695 (Δ -0.014 [-0.044, +0.009]) drop
  - FINAL ['log_rank']: AUC 0.709; vs log_pick Δ +0.011 [-0.079, +0.107]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.213 (base 0.246)
  - calibration: 0-15%: 12% pred / 25% actual (n=4) · 15-35%: 24% pred / 22% actual (n=23) · 35-60%: 46% pred / 45% actual (n=20) · 60-80%: 71% pred / 78% actual (n=18) · 80-100%: 86% pred / 0% actual (n=1)

## TE · Drafted + Combine (n=213; safe 11%, upside 3%)
- **safe** anchors: log_pick 0.899 · log_rank 0.880 · both 0.896 → anchor = log_pick
  - +best_yard_share: AUC 0.898 (Δ -0.001 [-0.013, +0.012]) drop
  - +best_ypta: AUC 0.899 (Δ +0.001 [-0.012, +0.012]) drop
  - +breakout_age: AUC 0.898 (Δ -0.001 [-0.020, +0.020]) drop
  - +draft_age: AUC 0.897 (Δ -0.001 [-0.006, +0.004]) drop
  - +wt: AUC 0.898 (Δ -0.001 [-0.007, +0.006]) drop
  - +speed_score: AUC 0.885 (Δ -0.013 [-0.030, -0.001]) drop
  - +ht: AUC 0.892 (Δ -0.006 [-0.018, +0.002]) drop
  - FINAL ['log_pick']: AUC 0.899; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.019 [-0.010, +0.048]; Brier 0.066 (base 0.096)
  - calibration: 0-15%: 4% pred / 5% actual (n=176) · 15-35%: 24% pred / 16% actual (n=19) · 35-60%: 43% pred / 43% actual (n=7) · 60-80%: 69% pred / 57% actual (n=7) · 80-100%: 92% pred / 100% actual (n=4)
- up: too few hits (6)

## TE · Rounds 1-3 (n=52; safe 35%, upside 10%)
- **safe** anchors: log_pick 0.706 · log_rank 0.660 · both 0.708 → anchor = log_pick
  - +best_yard_share: AUC 0.740 (Δ +0.034 [-0.042, +0.118]) drop
  - +best_ypta: AUC 0.771 (Δ +0.065 [-0.021, +0.160]) drop
  - +breakout_age: AUC 0.830 (Δ +0.124 [+0.005, +0.262]) KEEP
  - +draft_age: AUC 0.828 (Δ -0.002 [-0.030, +0.025]) drop
  - +wt: AUC 0.819 (Δ -0.011 [-0.064, +0.028]) drop
  - +speed_score: AUC 0.848 (Δ +0.018 [-0.028, +0.069]) drop
  - +ht: AUC 0.825 (Δ -0.005 [-0.021, +0.007]) drop
  - FINAL ['log_pick', 'breakout_age']: AUC 0.830; vs log_pick Δ +0.126 [+0.003, +0.270]; vs log_rank Δ +0.170 [+0.045, +0.309]; Brier 0.148 (base 0.226)
  - calibration: 0-15%: 8% pred / 11% actual (n=19) · 15-35%: 24% pred / 22% actual (n=9) · 35-60%: 45% pred / 38% actual (n=13) · 60-80%: 73% pred / 78% actual (n=9) · 80-100%: 95% pred / 100% actual (n=2)
- up: too few hits (5)
