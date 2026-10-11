"""DraftKings NFL Classic single-entry baseline optimizer. Educational analysis, not a prediction."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint

POSITIONS = ('QB', 'RB', 'WR', 'TE', 'DST')

def optimize(csv_path, output_dir='output', projection_file=None, count=3):
    df = pd.read_csv(csv_path)
    needed = {'Position','Name','ID','Salary','Game Info','TeamAbbrev','AvgPointsPerGame','Status'}
    if not needed.issubset(df.columns):
        raise ValueError('Missing salary columns: '+str(needed-set(df.columns)))
    df['Status'] = df['Status'].fillna('').str.upper().str.strip()
    df = df[~df.Status.isin(['IR','OUT','O','D'])].copy()
    df['Projection'] = pd.to_numeric(df.AvgPointsPerGame, errors='coerce').fillna(0)
    if projection_file:
        proj = pd.read_csv(projection_file)
        if not {'ID','Projection'}.issubset(proj.columns):
            raise ValueError('Projections file must contain ID and Projection columns')
        df = df.drop(columns='Projection').merge(proj[['ID','Projection']], on='ID', how='left')
        df['Projection'] = pd.to_numeric(df.Projection, errors='coerce')
        df = df.dropna(subset=['Projection'])
    df = df.reset_index(drop=True)
    n=len(df); pos=df.Position.to_numpy(); salary=df.Salary.to_numpy(); teams=df.TeamAbbrev.to_numpy()
    games=df['Game Info'].str.split(' ').str[0].to_numpy()
    opponent={}
    for g in set(games):
        if '@' in g:
            a,b=g.split('@',1);opponent[a]=b;opponent[b]=a
    constraints=[]
    def add(mask,lo,hi):
        constraints.append((np.asarray(mask,dtype=float),lo,hi))
    add(np.ones(n),9,9)
    add(salary,0,50000)
    for p,lo,hi in [('QB',1,1),('RB',2,3),('WR',3,4),('TE',1,2),('DST',1,1)]:
        add(pos==p,lo,hi)
    # The 7 non-QB/DST positions must total seven, leaving exactly one FLEX.
    # Force at least two distinct NFL teams using binary auxiliary indicators.
    unique_teams=sorted(set(teams));m=len(unique_teams);total=n+m
    A=[];lower=[];upper=[]
    for arr,lo,hi in constraints:
        row=np.zeros(total);row[:n]=arr;A.append(row);lower.append(lo);upper.append(hi)
    for j,t in enumerate(unique_teams):
        idx=np.flatnonzero(teams==t)
        row=np.zeros(total);row[idx]=1;row[n+j]=-9
        A.append(row);lower.append(-np.inf);upper.append(0)
        row=np.zeros(total);row[idx]=-1;row[n+j]=1
        A.append(row);lower.append(-np.inf);upper.append(0)
    row=np.zeros(total);row[n:]=1;A.append(row);lower.append(2);upper.append(np.inf)
    # Avoid using DST against offensive players facing that defense.
    for i in np.flatnonzero(pos=='DST'):
        opposing=opponent.get(teams[i])
        if opposing:
            row=np.zeros(total);row[i]=8;row[:n]+=((teams==opposing)&(pos!='DST')).astype(float)
            A.append(row);lower.append(-np.inf);upper.append(8)
    base=np.asarray(A);lo=np.asarray(lower);hi=np.asarray(upper)
    c=np.r_[-df.Projection.to_numpy(dtype=float),np.zeros(m)]
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    results=[]
    for rank in range(count):
        sol=milp(c,integrality=np.ones(total),bounds=Bounds(np.zeros(total),np.ones(total)),constraints=LinearConstraint(base,lo,hi),options={'time_limit':30,'mip_rel_gap':0.002})
        if sol.x is None:break
        chosen=np.flatnonzero(sol.x[:n]>.5)
        lineup=df.iloc[chosen].copy()
        # Label FLEX as the third RB, fourth WR, or second TE, as appropriate.
        lineup['Slot']=lineup.Position
        for p,required in [('RB',2),('WR',3),('TE',1)]:
            ids=lineup.index[lineup.Position==p].tolist()
            if len(ids)>required:lineup.loc[ids[-1],'Slot']='FLEX'
        lineup['Rank']=rank+1
        results.append(lineup)
        row=np.zeros(total);row[chosen]=1
        base=np.vstack([base,row]);lo=np.r_[lo,-np.inf];hi=np.r_[hi,7]
    if not results:raise RuntimeError('No valid lineup found')
    combined=pd.concat(results,ignore_index=True)
    combined[['Rank','Slot','Name','ID','TeamAbbrev','Salary','Projection','Status','Game Info']].to_csv(out/'candidate_lineups.csv',index=False)
    summary=combined.groupby('Rank').agg(Salary=('Salary','sum'),Baseline_Points=('Projection','sum'),Teams=('TeamAbbrev','nunique')).reset_index()
    summary.to_csv(out/'lineup_summary.csv',index=False)
    print(summary.to_string(index=False))
    print('Files saved in',out.resolve())
    return combined,summary

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--salaries',default='DKSalaries.csv')
    parser.add_argument('--projections',default=None)
    parser.add_argument('--output',default='output')
    args=parser.parse_args()
    optimize(args.salaries,args.output,args.projections)
