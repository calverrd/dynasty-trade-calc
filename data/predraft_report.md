# Pre-draft prospect model v1: build + validation report

Pool: 1679 players (1088 drafted, 1551 at the Combine), classes 2011-2026
pos
RB    527
TE    343
WR    809

Outcomes 2015-2024: 1474 players; source: {'sheet': 910, 'nflverse': 564}; safe rate 14.9%, upside rate 8.9%

College rows: 76822 player-seasons 2006-2025; columns ok: True
College match rate: 97.2% of pool, 97.5% of drafted players (by name only 56%, school-disambiguated 37%, most-recent-team 5%)
  WR: drafted matched 96.9% (n=516); 6+ game season found 93.2%
  RB: drafted matched 98.2% (n=339); 6+ game season found 94.7%
  TE: drafted matched 97.9% (n=233); 6+ game season found 91.8%

Wrote data/predraft_dataset.csv (1679 rows)

## WR · Drafted + Combine (n=709; safe 14%, upside 10%)
- **safe** anchors: log_pick 0.907 · log_rank 0.904 · both 0.905 → anchor = log_pick
  - +best_yard_share: AUC 0.902 (Δ -0.005 [-0.017, +0.005]) drop
  - +best_ypta: AUC 0.903 (Δ -0.004 [-0.015, +0.005]) drop
  - +final_ypta: AUC 0.905 (Δ -0.003 [-0.007, +0.002]) drop
  - +best_target_share: AUC 0.902 (Δ -0.005 [-0.018, +0.007]) drop
  - +breakout_age: AUC 0.896 (Δ -0.011 [-0.030, +0.005]) drop
  - +draft_age: AUC 0.907 (Δ -0.000 [-0.003, +0.003]) drop
  - +college_rush_capped: AUC 0.905 (Δ -0.002 [-0.004, -0.000]) drop
  - +wt: AUC 0.906 (Δ -0.001 [-0.004, +0.003]) drop
  - +speed_score: AUC 0.906 (Δ -0.001 [-0.004, +0.001]) drop
  - FINAL ['log_pick']: AUC 0.907; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.003 [-0.005, +0.011]; Brier 0.081 (base 0.120)
  - calibration: 0-15%: 5% pred / 4% actual (n=541) · 15-35%: 23% pred / 33% actual (n=81) · 35-60%: 47% pred / 53% actual (n=43) · 60-80%: 68% pred / 53% actual (n=19) · 80-100%: 91% pred / 80% actual (n=25)
- **up** anchors: log_pick 0.900 · log_rank 0.901 · both 0.900 → anchor = log_rank
  - +best_yard_share: AUC 0.899 (Δ -0.002 [-0.006, +0.001]) drop
  - +best_ypta: AUC 0.899 (Δ -0.002 [-0.006, +0.001]) drop
  - +final_ypta: AUC 0.898 (Δ -0.003 [-0.005, -0.001]) drop
  - +best_target_share: AUC 0.898 (Δ -0.003 [-0.006, +0.000]) drop
  - +breakout_age: AUC 0.898 (Δ -0.003 [-0.012, +0.005]) drop
  - +draft_age: AUC 0.903 (Δ +0.002 [-0.003, +0.006]) drop
  - +college_rush_capped: AUC 0.899 (Δ -0.001 [-0.004, +0.000]) drop
  - +wt: AUC 0.901 (Δ +0.001 [-0.006, +0.008]) drop
  - +speed_score: AUC 0.901 (Δ -0.000 [-0.002, +0.001]) drop
  - FINAL ['log_rank']: AUC 0.901; vs log_pick Δ +0.001 [-0.008, +0.009]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.068 (base 0.090)
  - calibration: 0-15%: 4% pred / 3% actual (n=581) · 15-35%: 24% pred / 34% actual (n=67) · 35-60%: 46% pred / 41% actual (n=34) · 60-80%: 70% pred / 56% actual (n=27)

## WR · Rounds 1-3 (n=189; safe 44%, upside 33%)
- **safe** anchors: log_pick 0.692 · log_rank 0.705 · both 0.704 → anchor = log_rank
  - +best_yard_share: AUC 0.711 (Δ +0.006 [-0.018, +0.031]) drop
  - +best_ypta: AUC 0.714 (Δ +0.009 [-0.016, +0.035]) drop
  - +final_ypta: AUC 0.702 (Δ -0.003 [-0.020, +0.013]) drop
  - +best_target_share: AUC 0.721 (Δ +0.016 [-0.015, +0.048]) drop
  - +breakout_age: AUC 0.727 (Δ +0.022 [-0.019, +0.063]) drop
  - +draft_age: AUC 0.707 (Δ +0.001 [-0.017, +0.020]) drop
  - +college_rush_capped: AUC 0.697 (Δ -0.008 [-0.026, +0.009]) drop
  - +wt: AUC 0.695 (Δ -0.010 [-0.027, +0.005]) drop
  - +speed_score: AUC 0.703 (Δ -0.002 [-0.025, +0.020]) drop
  - FINAL ['log_rank']: AUC 0.705; vs log_pick Δ +0.013 [-0.028, +0.055]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.214 (base 0.247)
  - calibration: 15-35%: 27% pred / 27% actual (n=75) · 35-60%: 47% pred / 43% actual (n=72) · 60-80%: 70% pred / 84% actual (n=32) · 80-100%: 81% pred / 60% actual (n=10)
- **up** anchors: log_pick 0.622 · log_rank 0.653 · both 0.637 → anchor = log_rank
  - +best_yard_share: AUC 0.651 (Δ -0.003 [-0.028, +0.022]) drop
  - +best_ypta: AUC 0.652 (Δ -0.001 [-0.029, +0.025]) drop
  - +final_ypta: AUC 0.631 (Δ -0.022 [-0.037, -0.008]) drop
  - +best_target_share: AUC 0.652 (Δ -0.001 [-0.025, +0.021]) drop
  - +breakout_age: AUC 0.652 (Δ -0.002 [-0.037, +0.032]) drop
  - +draft_age: AUC 0.655 (Δ +0.002 [-0.031, +0.033]) drop
  - +college_rush_capped: AUC 0.642 (Δ -0.011 [-0.024, +0.000]) drop
  - +wt: AUC 0.652 (Δ -0.002 [-0.032, +0.029]) drop
  - +speed_score: AUC 0.656 (Δ +0.002 [-0.020, +0.024]) drop
  - FINAL ['log_rank']: AUC 0.653; vs log_pick Δ +0.031 [-0.011, +0.076]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.209 (base 0.222)
  - calibration: 0-15%: 14% pred / 50% actual (n=2) · 15-35%: 25% pred / 25% actual (n=118) · 35-60%: 46% pred / 50% actual (n=58) · 60-80%: 63% pred / 36% actual (n=11)

## RB · Drafted + Combine (n=474; safe 19%, upside 11%)
- **safe** anchors: log_pick 0.874 · log_rank 0.861 · both 0.871 → anchor = log_pick
  - +best_yard_share: AUC 0.874 (Δ -0.000 [-0.007, +0.006]) drop
  - +best_target_share: AUC 0.876 (Δ +0.002 [-0.008, +0.013]) drop
  - +best_rush_share: AUC 0.871 (Δ -0.003 [-0.007, +0.001]) drop
  - +best_scrim_pg: AUC 0.870 (Δ -0.004 [-0.012, +0.003]) drop
  - +draft_age: AUC 0.874 (Δ -0.000 [-0.003, +0.003]) drop
  - +wt: AUC 0.874 (Δ -0.000 [-0.004, +0.004]) drop
  - +speed_score: AUC 0.870 (Δ -0.004 [-0.011, +0.000]) drop
  - +breakout_age: AUC 0.876 (Δ +0.002 [-0.003, +0.008]) drop
  - FINAL ['log_pick']: AUC 0.874; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.013 [-0.002, +0.028]; Brier 0.098 (base 0.151)
  - calibration: 0-15%: 6% pred / 7% actual (n=315) · 15-35%: 22% pred / 21% actual (n=81) · 35-60%: 47% pred / 45% actual (n=33) · 60-80%: 68% pred / 62% actual (n=21) · 80-100%: 91% pred / 92% actual (n=24)
- **up** anchors: log_pick 0.856 · log_rank 0.857 · both 0.858 → anchor = log_rank
  - +best_yard_share: AUC 0.866 (Δ +0.009 [-0.003, +0.022]) drop
  - +best_target_share: AUC 0.868 (Δ +0.010 [-0.005, +0.027]) drop
  - +best_rush_share: AUC 0.858 (Δ +0.001 [-0.007, +0.010]) drop
  - +best_scrim_pg: AUC 0.857 (Δ -0.000 [-0.010, +0.009]) drop
  - +draft_age: AUC 0.858 (Δ +0.001 [-0.003, +0.006]) drop
  - +wt: AUC 0.854 (Δ -0.003 [-0.008, +0.001]) drop
  - +speed_score: AUC 0.851 (Δ -0.006 [-0.020, +0.006]) drop
  - +breakout_age: AUC 0.870 (Δ +0.013 [+0.000, +0.030]) KEEP
  - FINAL ['log_rank', 'breakout_age']: AUC 0.870; vs log_pick Δ +0.014 [-0.003, +0.037]; vs log_rank Δ +0.013 [+0.000, +0.029]; Brier 0.069 (base 0.094)
  - calibration: 0-15%: 4% pred / 4% actual (n=380) · 15-35%: 24% pred / 24% actual (n=51) · 35-60%: 48% pred / 50% actual (n=30) · 60-80%: 69% pred / 69% actual (n=13)

## RB · Rounds 1-3 (n=94; safe 59%, upside 38%)
- **safe** anchors: log_pick 0.739 · log_rank 0.688 · both 0.716 → anchor = log_pick
  - +best_yard_share: AUC 0.729 (Δ -0.011 [-0.059, +0.037]) drop
  - +best_target_share: AUC 0.772 (Δ +0.032 [-0.030, +0.100]) drop
  - +best_rush_share: AUC 0.726 (Δ -0.013 [-0.047, +0.018]) drop
  - +best_scrim_pg: AUC 0.727 (Δ -0.013 [-0.033, +0.003]) drop
  - +draft_age: AUC 0.732 (Δ -0.008 [-0.021, +0.006]) drop
  - +wt: AUC 0.728 (Δ -0.012 [-0.037, +0.010]) drop
  - +speed_score: AUC 0.731 (Δ -0.009 [-0.023, +0.003]) drop
  - +breakout_age: AUC 0.776 (Δ +0.036 [-0.028, +0.102]) drop
  - FINAL ['log_pick']: AUC 0.739; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.052 [-0.029, +0.135]; Brier 0.201 (base 0.243)
  - calibration: 15-35%: 31% pred / 40% actual (n=10) · 35-60%: 47% pred / 46% actual (n=46) · 60-80%: 70% pred / 71% actual (n=21) · 80-100%: 92% pred / 88% actual (n=17)
- **up** anchors: log_pick 0.722 · log_rank 0.705 · both 0.718 → anchor = log_pick
  - +best_yard_share: AUC 0.744 (Δ +0.023 [-0.045, +0.097]) drop
  - +best_target_share: AUC 0.778 (Δ +0.056 [-0.028, +0.145]) drop
  - +best_rush_share: AUC 0.708 (Δ -0.013 [-0.030, +0.000]) drop
  - +best_scrim_pg: AUC 0.734 (Δ +0.012 [-0.020, +0.048]) drop
  - +draft_age: AUC 0.724 (Δ +0.002 [-0.038, +0.041]) drop
  - +wt: AUC 0.704 (Δ -0.017 [-0.048, +0.008]) drop
  - +speed_score: AUC 0.728 (Δ +0.008 [-0.031, +0.047]) drop
  - +breakout_age: AUC 0.729 (Δ +0.008 [-0.023, +0.041]) drop
  - FINAL ['log_pick']: AUC 0.722; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.017 [-0.060, +0.094]; Brier 0.187 (base 0.236)
  - calibration: 0-15%: 13% pred / 40% actual (n=5) · 15-35%: 24% pred / 22% actual (n=49) · 35-60%: 46% pred / 40% actual (n=25) · 60-80%: 65% pred / 67% actual (n=6) · 80-100%: 94% pred / 100% actual (n=9)

## TE · Drafted + Combine (n=291; safe 11%, upside 3%)
- **safe** anchors: log_pick 0.894 · log_rank 0.881 · both 0.893 → anchor = log_pick
  - +best_yard_share: AUC 0.891 (Δ -0.003 [-0.013, +0.005]) drop
  - +best_ypta: AUC 0.892 (Δ -0.002 [-0.013, +0.008]) drop
  - +breakout_age: AUC 0.893 (Δ -0.001 [-0.012, +0.011]) drop
  - +draft_age: AUC 0.893 (Δ -0.001 [-0.005, +0.002]) drop
  - +wt: AUC 0.897 (Δ +0.003 [-0.006, +0.014]) drop
  - +speed_score: AUC 0.890 (Δ -0.004 [-0.016, +0.007]) drop
  - +ht: AUC 0.889 (Δ -0.006 [-0.013, +0.000]) drop
  - FINAL ['log_pick']: AUC 0.894; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.013 [-0.010, +0.037]; Brier 0.068 (base 0.101)
  - calibration: 0-15%: 4% pred / 5% actual (n=236) · 15-35%: 23% pred / 21% actual (n=24) · 35-60%: 44% pred / 39% actual (n=18) · 60-80%: 70% pred / 57% actual (n=7) · 80-100%: 91% pred / 100% actual (n=6)
- **up** anchors: log_pick 0.826 · log_rank 0.829 · both 0.829 → anchor = log_rank
  - +best_yard_share: AUC 0.846 (Δ +0.017 [-0.030, +0.066]) drop
  - +best_ypta: AUC 0.842 (Δ +0.013 [-0.037, +0.063]) drop
  - +breakout_age: AUC 0.820 (Δ -0.009 [-0.024, +0.004]) drop
  - +draft_age: AUC 0.827 (Δ -0.002 [-0.008, +0.001]) drop
  - +wt: AUC 0.837 (Δ +0.007 [-0.022, +0.040]) drop
  - +speed_score: AUC 0.819 (Δ -0.011 [-0.033, +0.006]) drop
  - +ht: AUC 0.832 (Δ +0.003 [-0.015, +0.022]) drop
  - FINAL ['log_rank']: AUC 0.829; vs log_pick Δ +0.004 [-0.043, +0.051]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.032 (base 0.033)
  - calibration: 0-15%: 3% pred / 3% actual (n=277) · 15-35%: 20% pred / 21% actual (n=14)

## TE · Rounds 1-3 (n=71; safe 35%, upside 11%)
- **safe** anchors: log_pick 0.730 · log_rank 0.668 · both 0.717 → anchor = log_pick
  - +best_yard_share: AUC 0.737 (Δ +0.007 [-0.054, +0.071]) drop
  - +best_ypta: AUC 0.759 (Δ +0.026 [-0.041, +0.101]) drop
  - +breakout_age: AUC 0.741 (Δ +0.011 [-0.065, +0.090]) drop
  - +draft_age: AUC 0.710 (Δ -0.020 [-0.075, +0.028]) drop
  - +wt: AUC 0.717 (Δ -0.013 [-0.065, +0.034]) drop
  - +speed_score: AUC 0.710 (Δ -0.020 [-0.074, +0.025]) drop
  - +ht: AUC 0.706 (Δ -0.024 [-0.051, -0.004]) drop
  - FINAL ['log_pick']: AUC 0.730; vs log_pick Δ +0.000 [+0.000, +0.000]; vs log_rank Δ +0.064 [-0.034, +0.163]; Brier 0.179 (base 0.228)
  - calibration: 0-15%: 14% pred / 33% actual (n=9) · 15-35%: 23% pred / 18% actual (n=34) · 35-60%: 45% pred / 44% actual (n=18) · 60-80%: 71% pred / 67% actual (n=6) · 80-100%: 92% pred / 100% actual (n=4)
- **up** anchors: log_pick 0.288 · log_rank 0.399 · both 0.300 → anchor = log_rank
  - +best_yard_share: AUC 0.534 (Δ +0.135 [-0.087, +0.323]) drop
  - +best_ypta: AUC 0.587 (Δ +0.185 [-0.073, +0.433]) drop
  - +breakout_age: AUC 0.421 (Δ +0.022 [-0.063, +0.106]) drop
  - +draft_age: AUC 0.375 (Δ -0.024 [-0.061, +0.000]) drop
  - +wt: AUC 0.383 (Δ -0.016 [-0.131, +0.084]) drop
  - +speed_score: AUC 0.468 (Δ +0.070 [-0.012, +0.184]) drop
  - +ht: AUC 0.405 (Δ +0.005 [-0.078, +0.086]) drop
  - FINAL ['log_rank']: AUC 0.399; vs log_pick Δ +0.112 [-0.044, +0.319]; vs log_rank Δ +0.000 [+0.000, +0.000]; Brier 0.106 (base 0.100)
  - calibration: 0-15%: 10% pred / 13% actual (n=60) · 15-35%: 18% pred / 0% actual (n=11)

# Continuous check: best two seasons (years 1-3) PPG, classes 2011-2023

## WR (n=668, mean B2S 3.4) anchor ['log_rank']: LOSO R² 0.570, MAE 2.17, R1-3 Spearman 0.391
  - +['best_ypta']: R² 0.570 (Δ -0.000 [-0.004, +0.004]); R1-3 Spearman 0.400 (Δ [-0.003, +0.023]) drop
  - +['breakout_age']: R² 0.571 (Δ +0.001 [-0.001, +0.003]); R1-3 Spearman 0.397 (Δ [-0.002, +0.015]) drop
  - +['teammate_dc']: R² 0.569 (Δ -0.001 [-0.002, -0.000]); R1-3 Spearman 0.390 (Δ [-0.006, +0.005]) drop
  - +['early_declare']: R² 0.570 (Δ +0.000 [-0.003, +0.003]); R1-3 Spearman 0.402 (Δ [-0.001, +0.023]) drop
  - +['best_ypta', 'teammate_dc', 'early_declare']: R² 0.569 (Δ -0.001 [-0.006, +0.004]); R1-3 Spearman 0.405 (Δ [-0.004, +0.034]) drop
  - +['best_yard_share']: R² 0.570 (Δ +0.000 [-0.004, +0.005]); R1-3 Spearman 0.403 (Δ [-0.003, +0.028]) drop
  - +['draft_age']: R² 0.570 (Δ -0.000 [-0.001, +0.001]); R1-3 Spearman 0.392 (Δ [-0.005, +0.007]) drop

## RB (n=444, mean B2S 3.9) anchor ['log_pick']: LOSO R² 0.550, MAE 2.57, R1-3 Spearman 0.402
  - +['best_rec_share']: R² 0.557 (Δ +0.008 [-0.003, +0.019]); R1-3 Spearman 0.436 (Δ [-0.003, +0.074]) drop
  - +['best_target_share']: R² 0.556 (Δ +0.007 [-0.004, +0.017]); R1-3 Spearman 0.433 (Δ [-0.002, +0.066]) drop
  - +['best_yds_per_team_play']: R² 0.551 (Δ +0.001 [-0.004, +0.006]); R1-3 Spearman 0.389 (Δ [-0.033, +0.002]) drop
  - +['best_rec_share', 'best_yds_per_team_play']: R² 0.556 (Δ +0.007 [-0.004, +0.018]); R1-3 Spearman 0.437 (Δ [-0.001, +0.076]) drop
  - +['best_target_share', 'tgt_x_early']: R² 0.556 (Δ +0.006 [-0.009, +0.022]); R1-3 Spearman 0.453 (Δ [-0.009, +0.121]) drop
  - +['ypp_x_late']: R² 0.556 (Δ +0.006 [-0.005, +0.019]); R1-3 Spearman 0.394 (Δ [-0.059, +0.041]) drop
  - +['wt']: R² 0.548 (Δ -0.002 [-0.003, -0.001]); R1-3 Spearman 0.398 (Δ [-0.012, +0.001]) drop
  - +['speed_score']: R² 0.547 (Δ -0.002 [-0.005, +0.001]); R1-3 Spearman 0.391 (Δ [-0.034, +0.006]) drop

## TE (n=274, mean B2S 3.2) anchor ['log_pick']: LOSO R² 0.562, MAE 1.84, R1-3 Spearman 0.499
  - +['breakout_age']: R² 0.562 (Δ +0.000 [-0.004, +0.005]); R1-3 Spearman 0.501 (Δ [-0.017, +0.026]) drop
  - +['best_ypta']: R² 0.562 (Δ +0.000 [-0.010, +0.010]); R1-3 Spearman 0.519 (Δ [-0.011, +0.060]) drop
  - +['hass']: R² 0.559 (Δ -0.002 [-0.005, +0.000]); R1-3 Spearman 0.495 (Δ [-0.017, +0.004]) drop
  - +['hass', 'pick_x_hass']: R² 0.569 (Δ +0.007 [-0.007, +0.024]); R1-3 Spearman 0.522 (Δ [-0.041, +0.091]) drop
  - +['breakout_age', 'best_ypta']: R² 0.563 (Δ +0.001 [-0.010, +0.012]); R1-3 Spearman 0.515 (Δ [-0.016, +0.054]) drop
  - +['wt']: R² 0.565 (Δ +0.004 [-0.010, +0.018]); R1-3 Spearman 0.504 (Δ [-0.043, +0.056]) drop
