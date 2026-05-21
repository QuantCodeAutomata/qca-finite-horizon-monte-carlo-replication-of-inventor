# Experiment 3 — Theoretical Verification

- **frozen_value_match**: True
- **v_closed_form**: -exp(-gamma*x)*exp(-gamma*q*s)*exp(gamma**2*q**2*sigma**2*(T - t)/2)
- **reservation_a_matches_paper**: True
- **reservation_b_matches_paper**: True
- **average_reservation_matches**: True
- **r_a_expression**: -T*gamma*q*sigma**2 + T*gamma*sigma**2/2 + gamma*q*sigma**2*t - gamma*sigma**2*t/2 + s
- **r_b_expression**: -T*gamma*q*sigma**2 - T*gamma*sigma**2/2 + gamma*q*sigma**2*t + gamma*sigma**2*t/2 + s
- **r_average_expression**: -T*gamma*q*sigma**2 + gamma*q*sigma**2*t + s
- **foc_term_matches_paper**: True
- **foc_term_expression**: (-log(k) + log(gamma + k))/gamma
- **max_spread_err**: 4.440892098500626e-16
- **max_midpoint_err**: 1.4210854715202004e-14

## limits

- r_minus_s_at_gamma=0.5: -10.0
- r_minus_s_at_gamma=0.1: -2.0
- r_minus_s_at_gamma=0.01: -0.20000000000000284
- r_minus_s_at_gamma=0.001: -0.01999999999999602
- delta_a_at_t=0.0: -1.1546147886242886
- delta_b_at_t=0.0: 2.845385211375712
- delta_a_at_t=0.5: -0.25461478862428844
- delta_b_at_t=0.5: 1.7453852113757118
- delta_a_at_t=0.9: 0.46538521137571165
- delta_b_at_t=0.9: 0.8653852113757116
- delta_a_at_t=0.99: 0.6273852113757116
- delta_b_at_t=0.99: 0.6673852113757116
- delta_a_at_t=1.0: 0.6453852113757116
- delta_b_at_t=1.0: 0.6453852113757116
