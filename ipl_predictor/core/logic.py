# core/logic.py

from .team_builder import predict_xi
from .utils import simulate_win_percentage
import random
import pandas as pd  # ✅ required for DataFrame operations

def get_predictions(df_players, df_stadiums, team_a, captain_a, team_b, captain_b, venue):
    df_stadiums.columns = df_stadiums.columns.str.strip()
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

    xi_a = predict_xi(df_players, team_a, captain_a, pitch_type, bowling_type, batting_bias, bowling_bias)
    xi_b = predict_xi(df_players, team_b, captain_b, pitch_type, bowling_type, batting_bias, bowling_bias)

    score_a = sum(player['FitScore'] for player in xi_a)
    score_b = sum(player['FitScore'] for player in xi_b)
    win_a, win_b = simulate_win_percentage(score_a, score_b)

    return xi_a, xi_b, win_a, win_b

def generate_shuffled_xi(df_players, team_name, captain_name, pitch_type, bowling_type, batting_bias, bowling_bias):
    team_df = df_players[df_players['Team'].str.lower() == team_name.lower()]
    
    # Ensure captain is fixed
    captain_row = team_df[team_df['Player Name'] == captain_name]
    other_players = team_df[team_df['Player Name'] != captain_name]

    # Shuffle the remaining players
    shuffled_others = other_players.sample(frac=1, random_state=random.randint(0, 10000))
    shuffled_team = pd.concat([captain_row, shuffled_others])

    return predict_xi(shuffled_team, team_name, captain_name, pitch_type, bowling_type, batting_bias, bowling_bias)
