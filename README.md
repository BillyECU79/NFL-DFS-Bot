# NFL DFS V7 — Contest Selector (research prototype)

## Run on Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Or run `python contest_selector.py --contest 'Spy $100 (1-max)'`.

## What is new
- Four contest presets: $100 1-max, $150 3-max, $555 5-max, $333 125-max (user enters up to three).
- Match screenshot projections to DraftKings IDs and verify position, salary and team.
- Generate up to 45 candidate lineups and select 1 or 3 depending on contest.
- Prefer QB/WR or QB/TE correlation, while accounting heuristically for projection, ceiling and ownership.
- Show and export selected lineups, plus top candidate rankings.

## Important limitations
- Only 71 player projections from screenshots were transcribed into the source file. **Not the entire slate.** Players absent from the projection file are excluded.
- No verified live injury/starting status; questionable players require manual confirmation.
- Ownership values are third-party estimates, not observed ownership.
- The ranking formula is a heuristic, **not calibrated ROI or expected payout**. Sum of individual ceilings is not a lineup ceiling.
- No validated field simulation or payout-aware ranking yet. Contest payouts remain included for later integration.
- Do not automate DraftKings entry. Review lineup and contest rules manually.
