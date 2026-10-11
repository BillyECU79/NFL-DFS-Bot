from pathlib import Path
import pandas as pd
import streamlit as st
from contest_selector import CONTESTS,run,validate_inputs
ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='NFL DFS Contest Lab',layout='wide')
st.title('NFL DFS • Single-entry and small-portfolio lab')
st.warning('Research-only prototype. Only 71 screenshot-matched projections are currently available. No live inactives or validated ownership/ROI model. Do not treat rankings as guaranteed or calibrated.')
contest=st.selectbox('Choose tournament',list(CONTESTS))
config=CONTESTS[contest]
a,b,c=st.columns(3)
a.metric('Contest field',f"{config['field']:,}")
b.metric('Entry fee',f"${config['fee']:,}")
c.metric('Lineups to generate',config['entries'])
with st.expander('Review / edit screenshot projections'):
 p=pd.read_csv(ROOT/'screenshot_projections.csv',dtype={'ID':str})
 edit=st.data_editor(p,hide_index=True,num_rows='fixed',use_container_width=True)
 if st.button('Save changes'):
  edit.to_csv(ROOT/'screenshot_projections.csv',index=False)
  st.success('Saved. Validate projections before running.')
try:
 s,p=validate_inputs()
 st.info(f"{len(p)} of {len(s)} DraftKings player IDs have matched projections. Missing players are excluded, not assigned fabricated values.")
except Exception as exc:st.error(str(exc));st.stop()
if st.button('Generate and compare lineups',type='primary'):
 try:
  with st.spinner('Optimizing and scoring candidates...'):
   lineups,ranked=run(contest)
  st.session_state['lineups']=lineups
  st.session_state['ranked']=ranked
 except Exception as exc:st.error(str(exc))
if 'lineups' in st.session_state:
 data=st.session_state['lineups']
 for entry,g in data.groupby('Entry'):
  st.subheader(f"Lineup {entry} — ${g.Salary.sum():,} · {g.Projection.sum():.2f} projected")
  st.dataframe(g[['Slot','Name','TeamAbbrev','Salary','Projection','Ceiling','Ownership','Status']],hide_index=True,use_container_width=True)
 st.download_button('Download selected lineups CSV',data.to_csv(index=False).encode(),'selected_lineups.csv','text/csv')
 st.subheader('Candidate comparison')
 st.dataframe(st.session_state['ranked'].head(15),hide_index=True,use_container_width=True)
st.caption('Contest selection changes heuristic scoring and entry count; payout EV is NOT calculated. Review every entry manually before submission.')
