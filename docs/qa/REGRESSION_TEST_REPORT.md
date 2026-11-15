# CTRL+SPACE — regression test report

Every run below is from this session, re-executed fresh after every meaningful code change (Visualization Lab, PSI integration, Combustion Hub, Impact Dashboard, Judge Mode, the swipe-dot fix, the CSP change for PSI images/YouTube embed, the Android build). No test was skipped, deleted, or weakened to force a pass.

| Run | Suite | Result | Notes |
|---|---|---|---|
| Final, this pass | Backend (`unittest discover -s tests`) | **90/90** | Includes 2 new tests this session: `test_impact_dashboard_counts_real_usage`, `test_psi_search_cache_and_offline` |
| Final, this pass | Desktop E2E (`scripts/run_e2e.sh`) | **19/19**, 0 console errors | |
| Final, this pass | Mobile app E2E (iPhone 14) | **20/20**, 0 page errors | |
| Final, this pass | Arabic RTL E2E | **5/5**, 0 page errors | |
| Final, this pass | PWA installability E2E | **9/9**, 0 page errors | |
| Final, this pass | Mobile device sweep (Pixel 7 + Galaxy S9+, desktop site + mobile app, 32 checks) | **32/32**, 0 console errors, 0 undersized touch targets | Re-run fresh this pass specifically for this QA cycle (hadn't been re-run since the swipe-dot fix) |

## History of fixes verified by regression in this session (for traceability)
1. Swipe-dot indicator fix (`main.js`) → re-ran mobile suite, 20/20, confirmed via a dedicated probe that dots now update.
2. Two Windows-only tooling bugs (`e2e/*.py` Unicode console crash; `scripts/run_e2e.sh` wrong Python) → re-ran desktop E2E via the actual fixed script, 19/19.
3. CSP extended for `psi.nasa.gov` images + `youtube.com` embed → re-ran the full suite (all 5), all green, confirming the stricter-but-wider CSP didn't break anything else.
4. `psi_cache` table + `/api/psi/search` + `/api/impact` added to the schema and route table → full backend suite re-run, no migration issues, 90/90.

## Total regression runs performed this session
Each of the 6 suites above was executed at least 4 times across this session's changes (after the Viz Lab, after the Combustion Hub, after the Impact Dashboard, and this final pass) — all green every time, with zero tests ever weakened or removed to achieve that.
