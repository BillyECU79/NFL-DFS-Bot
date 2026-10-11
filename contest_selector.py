"""Research-only lineup selection. Scores are heuristics, NOT predicted ROI."""
from pathlib import Path
import pandas as pd
from optimizer import optimize

ROOT=Path(__file__).resolve().parent
CONTESTS={
 'Spy $100 (1-max)':{'fee':100,'field':4444,'entries':1,'max_entries':1,'ceiling_weight':.22,'ownership_penalty':.045},
 'Power Sweep $150 (3-max)':{'fee':150,'field':1851,'entries':3,'max_entries':3,'ceiling_weight':.20,'ownership_penalty':.035},
 'Facemask $555 (5-max)':{'fee':555,'field':500,'entries':3,'max_entries':5,'ceiling_weight':.15,'ownership_penalty':.020},
 'Wildcat $333 (125-max)':{'fee':333,'field':4170,'entries':3,'max_entries':125,'ceiling_weight':.25,'ownership_penalty':.055},
}

def validate_inputs():
 s=pd.read_csv(ROOT/'DKSalaries.csv',dtype={'ID':str})
 p=pd.read_csv(ROOT/'screenshot_projections.csv',dtype={'ID':str})
 if p.ID.duplicated().any():raise ValueError('Duplicate projection player IDs')
 if not p.ID.isin(s.ID).all():raise ValueError('Projection IDs absent from salary file')
 matched=p.merge(s[['ID','Name','Position','Salary','TeamAbbrev','Status']],on='ID',suffixes=('_p','_dk'),validate='one_to_one')
 bad=matched[(matched.Salary_p!=matched.Salary_dk)|(matched.Position_p!=matched.Position_dk)|(matched.Team!=matched.TeamAbbrev)]
 if len(bad):raise ValueError('Mismatched projections: '+bad[['ID','Name_p','Name_dk']].to_string(index=False))
 for col in ['Projection','Ceiling','Ownership']:
  if p[col].isna().any():raise ValueError('Missing '+col)
 if ((p.Ownership<0)|(p.Ownership>100)).any():raise ValueError('Ownership outside 0-100')
 return s,p

def lineup_score(g,c):
 cfg=CONTESTS[c]
 proj=float(g.Projection.sum()); ceiling=float(g.Ceiling.sum()); own=float(g.Ownership.sum())
 qb=g[g.Position=='QB'].iloc[0]; targets=g[(g.TeamAbbrev==qb.TeamAbbrev)&g.Position.isin(['WR','TE'])]
 # Correlation is a transparent structural bonus, not an estimated probability.
 stack_bonus=2.0*min(len(targets),2)
 if len(targets)==0:stack_bonus=-4.0
 # Conservative ownership penalty: total ownership is not duplication probability.
 score=proj+cfg['ceiling_weight']*(ceiling-proj)-cfg['ownership_penalty']*own+stack_bonus
 return score, len(targets)

def run(contest='Spy $100 (1-max)', candidate_count=45):
 if contest not in CONTESTS:raise ValueError('Unknown contest')
 s,p=validate_inputs()
 merged=s.merge(p[['ID','Projection','Ceiling','Ownership']],on='ID',how='inner',validate='one_to_one')
 merged['Status']=merged.Status.fillna('').astype(str).str.upper().str.strip()
 merged=merged[~merged.Status.isin(['OUT','IR','O','D'])].copy()
 merged['RankPoints']=merged.Projection+.16*(merged.Ceiling-merged.Projection)-.028*merged.Ownership
 out=ROOT/'output_v7';out.mkdir(exist_ok=True)
 salaries=out/'eligible_salaries.csv';ranking=out/'rank_input.csv'
 merged.drop(columns=['Projection','Ceiling','Ownership','RankPoints']).to_csv(salaries,index=False)
 merged[['ID','RankPoints']].rename(columns={'RankPoints':'Projection'}).to_csv(ranking,index=False)
 candidates,_=optimize(salaries,out/'candidate_solver',ranking,count=candidate_count)
 candidates['ID']=candidates.ID.astype(str)
 candidates=candidates.drop(columns='Projection').merge(p[['ID','Projection','Ceiling','Ownership']],on='ID',how='left',validate='many_to_one')
 ranks=[]
 for rank,g in candidates.groupby('Rank'):
  score,stack=lineup_score(g,contest)
  ranks.append({'Candidate':int(rank),'HeuristicScore':round(score,3),'ProjectedPoints':round(g.Projection.sum(),2),'Salary':int(g.Salary.sum()),'QBSTackTargets':stack,'MeanOwnership':round(g.Ownership.mean(),2)})
 ranked=pd.DataFrame(ranks).sort_values('HeuristicScore',ascending=False)
 selected=[];ids=[]
 for r in ranked.itertuples():
  g=candidates[candidates.Rank==r.Candidate]
  players=set(g.ID)
  # For 3-entry portfolio, require at least 2 different players from previously selected lineups.
  if any(len(players & prev)>7 for prev in ids):continue
  selected.append((r.Candidate,g));ids.append(players)
  if len(selected)==CONTESTS[contest]['entries']:break
 if len(selected)<CONTESTS[contest]['entries']:raise RuntimeError('Insufficient diverse candidates')
 final=[]
 for i,(_,g) in enumerate(selected,1):
  x=g.copy();x['Entry']=i;x['Contest']=contest;final.append(x)
 result=pd.concat(final,ignore_index=True)
 result[['Contest','Entry','Slot','Name','ID','Position','TeamAbbrev','Salary','Projection','Ceiling','Ownership','Status']].to_csv(out/'selected_lineups.csv',index=False)
 ranked.to_csv(out/'candidate_rankings.csv',index=False)
 print('Contest:',contest,'| eligible projections:',len(merged),'| candidate lineups:',len(ranked))
 for i,g in result.groupby('Entry'):
  print('\nENTRY',i,'salary',g.Salary.sum(),'projection',round(g.Projection.sum(),2))
  print(g[['Slot','Name','Salary','Projection','Ownership']].to_string(index=False))
 print('\nRESEARCH ONLY: Heuristic score is NOT expected value. Verify starters, injuries and slate eligibility.')
 return result,ranked

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--contest',choices=list(CONTESTS),default='Spy $100 (1-max)');args=parser.parse_args()
 run(args.contest)
