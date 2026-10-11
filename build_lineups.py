from pathlib import Path
import pandas as pd
from optimizer import optimize
BASE=Path(__file__).resolve().parent
s=pd.read_csv(BASE/'DKSalaries.csv',dtype={'ID':str})
p=pd.read_csv(BASE/'screenshot_projections.csv',dtype={'ID':str})
# Only screenshot-verified projections are eligible. No heuristic filler.
p=p.drop_duplicates('ID')
s=s.merge(p[['ID','Projection','Ceiling','Ownership']],on='ID',how='inner',validate='one_to_one')
s['Status']=s.Status.fillna('').astype(str).str.upper().str.strip()
s=s[~s.Status.isin(['OUT','IR','O','D'])].copy()
# Own-based adjustment is a transparent exploratory ranking, not calibrated EV.
s['RankingPoints']=s.Projection + 0.13*(s.Ceiling-s.Projection) - 0.025*s.Ownership
out=BASE/'output';out.mkdir(exist_ok=True)
# optimizer expects original CSV columns and projection keyed by ID
s.drop(columns=['Projection','Ceiling','Ownership','RankingPoints']).to_csv(out/'eligible_salaries.csv',index=False)
s[['ID','RankingPoints']].rename(columns={'RankingPoints':'Projection'}).to_csv(out/'ranking_input.csv',index=False)
lineups,_=optimize(out/'eligible_salaries.csv',out/'solver',out/'ranking_input.csv',count=3)
lineups['ID']=lineups['ID'].astype(str)
lineups=lineups.drop(columns='Projection').merge(p[['ID','Projection','Ceiling','Ownership']],on='ID',how='left',validate='many_to_one')
lineups[['Rank','Slot','Name','ID','TeamAbbrev','Salary','Projection','Ceiling','Ownership','Status']].to_csv(out/'lineups.csv',index=False)
summary=lineups.groupby('Rank').agg(Salary=('Salary','sum'),Projected_Points=('Projection','sum'),Sum_Individual_Ceilings=('Ceiling','sum'),Avg_Ownership=('Ownership','mean')).round(2)
summary.to_csv(out/'summary.csv')
print('\nCANDIDATE LINEUPS (screenshot projection subset only)')
for rank,grp in lineups.groupby('Rank'):
 print('\nLINEUP',rank,'salary',grp.Salary.sum(),'projection',round(grp.Projection.sum(),2))
 print(grp[['Slot','Name','Salary','Projection','Ownership']].to_string(index=False))
print('\nCAUTION: Individual ceilings cannot simply be added to estimate a lineup ceiling. These are unvalidated candidates, not final picks.')
