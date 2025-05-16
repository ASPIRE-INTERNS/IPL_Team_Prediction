# core/team_builder.py
import pandas as pd
from .scoring import calculate_batting_score, calculate_bowling_score, calculate_fit_score

def predict_xi(df, team_name, captain_name, pitch_type, bowling_type, batting_bias, bowling_bias):
    team = df[df['Team'].str.lower() == team_name.lower()].copy()
    team['Batting Score'] = team.apply(lambda row: calculate_batting_score(row, batting_bias), axis=1)
    team['Bowling Score'] = team.apply(lambda row: calculate_bowling_score(row, bowling_bias), axis=1)
    team['FitScore'] = team.apply(lambda row: calculate_fit_score(row, pitch_type, bowling_type, batting_bias, bowling_bias), axis=1)

    if captain_name not in team['Player Name'].values:
        return []

    # Role targets
    role_targets = {'batsman': 5, 'bowler': 4, 'allrounder': 2}
    if pitch_type == 1:
        role_targets = {'batsman': 5, 'bowler': 3, 'allrounder': 3}
    elif pitch_type == 0:
        role_targets = {'batsman': 4, 'bowler': 4, 'allrounder': 3}

    selected, selected_names = [], set()
    overseas = 0
    indians = 0

    captain = team[team['Player Name'] == captain_name].iloc[0]
    selected.append(captain.to_dict())
    selected_names.add(captain_name)
    overseas += int(captain['Nationality'] == 0)
    indians += int(captain['Nationality'] == 1)

    role = captain['Primary role'].lower()
    counts = {'batsman': 0, 'bowler': 0, 'allrounder': 0}
    if 'all-rounder' in role: counts['allrounder'] += 1
    elif 'bowler' in role: counts['bowler'] += 1
    else: counts['batsman'] += 1

    def get_pool(role):
        return team[(team['Primary role'].str.contains(role, case=False)) &
                    (~team['Player Name'].isin(selected_names))].sort_values(by='FitScore', ascending=False)

    for r in ['batsman', 'bowler', 'allrounder']:
        needed = role_targets[r] - counts[r]
        pool = get_pool('All-rounder' if r == 'allrounder' else r.capitalize())

        for _, player in pool.iterrows():
            if needed == 0 or len(selected) >= 11:
                break
            if player['Nationality'] == 0 and overseas >= 4:
                continue
            if player['Nationality'] == 1 and indians >= 7:
                continue
            selected.append(player.to_dict())
            selected_names.add(player['Player Name'])
            overseas += int(player['Nationality'] == 0)
            indians += int(player['Nationality'] == 1)
            needed -= 1

    if len(selected) < 11:
        filler = team[~team['Player Name'].isin(selected_names)].sort_values(by='FitScore', ascending=False)
        for _, player in filler.iterrows():
            if player['Nationality'] == 0 and overseas >= 4: continue
            if player['Nationality'] == 1 and indians >= 7: continue
            selected.append(player.to_dict())
            if len(selected) == 11: break

    df_final = pd.DataFrame(selected).sort_values(by='FitScore', ascending=False).reset_index(drop=True)
    df_final.loc[df_final['Player Name'] == captain_name, 'Player Name'] += ' (Captain)'
    return df_final.to_dict('records')
