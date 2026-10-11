# NFL DFS Version 8 — Screenshot Player Pool

This update replaces Version 7 and keeps the same Streamlit dashboard and contest selector.

## What changed
- 197 screenshot rows manually transcribed across QB, RB, WR, TE and DST.
- All 197 matched to an exact DraftKings player ID and position. Players not in the screenshots are excluded.
- The app still uses a **heuristic** lineup ranking, NOT validated expected return.
- All projections are snapshots provided by the user; they are not updated live.
- Screenshots were manually transcribed. Check critical values and statuses before entering contests.
- Questionable players remain eligible but require injury/inactive review. OUT/IR players are excluded.
- The program does not submit lineups to DraftKings.

## Update your existing Mac installation
1. Stop the old Streamlit app in Terminal with **Control+C**.
2. Unzip Version 8. Open its folder and copy **all files except `.venv`** into your existing `NFL_DFS_V7_Contest_Selector` folder, choosing **Replace** when asked. (Do not delete `.venv`.)
3. In the same Terminal, while inside the original folder, run `source .venv/bin/activate` if needed and then `python -m streamlit run app.py`.
4. If Streamlit is still running, refresh the browser. Verify the matched projection count is **197**.
5. To update GitHub, upload the new files to the existing repository and commit changes. No new repository is needed.

## Important
The current contest-specific scoring and opponent simulations have NOT been historically calibrated. The screenshots' displayed ceilings are provider-defined values, not verified statistical percentiles. Do not interpret these lineups as guaranteed or validated high-stakes recommendations. Check official inactives, team assignments, contest eligibility, and updated odds before locking lineups.
