import pandas as pd
import math

# 📥 Input
player_file = input("Enter player stats Excel file (e.g., Final.xlsx): ").strip()
stadium_file = input("Enter stadium stats Excel file (e.g., Stadium data.xlsx): ").strip()
team_a = input("Enter Team A name: ").strip()
team_b = input("Enter Team B name: ").strip()
venue = input("Enter Stadium/Venue name: ").strip()

# 📄 Load Data
df_players = pd.read_excel(player_file)
df_stadiums = pd.read_excel(stadium_file)
df_stadiums.columns = df_stadiums.columns.str.strip()

# 🏟️ Stadium Logic
stadium_row = df_stadiums[df_stadiums['Stadium Name'].str.contains(venue, case=False, na=False)]
batting_bias, bowling_bias, pitch_type, bowling_type = 1, 1, '', ''

if not stadium_row.empty:
    first_wins = int(stadium_row['Batting First Won'].values[0])
    second_wins = int(stadium_row['Batting Second Won'].values[0])
    total = first_wins + second_wins
    if total > 0:
        batting_bias = (second_wins + 1) / (first_wins + 1)
        bowling_bias = (first_wins + 1) / (second_wins + 1)
    pitch_type = stadium_row['Pitch Type'].values[0]
    bowling_type = stadium_row['Bowling Type'].values[0] if 'Bowling Type' in stadium_row else ''

# 🎯 Scoring functions
def calculate_batting_score(row):
    try:
        inns = float(row.get('T20s - Batting - Inns', 1))
        eff = float(row['T20s - Batting - Ave']) + float(row['T20s - Batting - SR']) / 2
        return eff * math.log(inns + 1) * batting_bias
    except:
        return 0

def calculate_bowling_score(row):
    try:
        inns = float(row.get('T20s - Bowling - Inns', 1))
        eff = (50 / (float(row['T20s - Bowling - Ave']) + 1)) +               (50 / (float(row['T20s - Bowling - Econ']) + 1)) +               (50 / (float(row['T20s - Bowling - SR']) + 1))
        return eff * math.log(inns + 1) * bowling_bias
    except:
        return 0

def calculate_fit_score(row, pitch_type, bowling_type):
    bat_score = calculate_batting_score(row)
    bowl_score = calculate_bowling_score(row)

    if 'All-rounder' in str(row['Primary role']):
        fit_score = (bat_score + bowl_score) / 2
    elif 'Bowler' in str(row['Primary role']):
        fit_score = bowl_score
    else:
        fit_score = bat_score

    if bowling_type == 'spin' and 'spin' in str(row['Bowling Type']).lower():
        fit_score *= 1.1
    elif bowling_type == 'pace' and ('fast' in str(row['Bowling Type']).lower() or 'medium' in str(row['Bowling Type']).lower()):
        fit_score *= 1.1

    return fit_score

# Apply FitScore to players
df_players['FitScore'] = df_players.apply(lambda row: calculate_fit_score(row, pitch_type, bowling_type), axis=1)

# 🎯 XI Selection Logic
def predict_xi(df, team_name, captain_name, pitch_type, bowling_type):
    team = df[df['Team'].str.lower() == team_name.lower()].copy()
    team['Batting Score'] = team.apply(calculate_batting_score, axis=1)
    team['Bowling Score'] = team.apply(calculate_bowling_score, axis=1)
    if captain_name not in team['Player Name'].values:
        print(f"❌ Captain '{captain_name}' not found in team '{team_name}'")
        return pd.DataFrame()

    # Role targets by pitch type
    if pitch_type == 1:
        role_targets = {'batsman': 5, 'bowler': 3, 'allrounder': 3}
    elif pitch_type == 0:
        role_targets = {'batsman': 4, 'bowler': 4, 'allrounder': 3}
    else:
        role_targets = {'batsman': 5, 'bowler': 4, 'allrounder': 2}

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

        if r == 'bowler' and pitch_type in [0, 1] and bowling_type in [0, 1]:
            pool = pool[pool['Bowling Type'] == bowling_type]

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
    return df_final[['Player Name', 'Primary role', 'Nationality', 'Batting Score', 'Bowling Score', 'FitScore']]

# 🎬 EXECUTE
captain_a = input(f"Enter captain for {team_a}: ").strip()
captain_b = input(f"Enter captain for {team_b}: ").strip()

print(f"\n📋 Best XI for {team_a} at {venue}")
team_a_xi = predict_xi(df_players, team_a, captain_a, pitch_type, bowling_type)
print(team_a_xi.to_string(index=False))

print(f"\n📋 Best XI for {team_b} at {venue}")
team_b_xi = predict_xi(df_players, team_b, captain_b, pitch_type, bowling_type)
print(team_b_xi.to_string(index=False))
