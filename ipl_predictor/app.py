from flask import Flask, render_template, request
import pandas as pd
from core.logic import get_predictions, generate_shuffled_xi
from core.utils import simulate_win_percentage

app = Flask(__name__)

# Load Excel files once
df_players = pd.read_excel("f.xlsx")
df_stadiums = pd.read_excel("s.xlsx")
df_stadiums.columns = df_stadiums.columns.str.strip()

teams = sorted(df_players['Team'].dropna().unique())
venues = sorted(df_stadiums['Stadium Name'].dropna().unique())

# Group players by team for dynamic dropdowns
players_by_team = df_players.groupby('Team')['Player Name'].apply(list).to_dict()

# lineup and predictor
@app.route("/", methods=["GET", "POST"])
def index():
    xi_a = xi_b = None
    win_a = win_b = None
    team_a = team_b = venue = ""

    if request.method == "POST":
        team_a = request.form["team_a"]
        captain_a = request.form["captain_a"]
        team_b = request.form["team_b"]
        captain_b = request.form["captain_b"]
        venue = request.form["venue"]

        xi_a, xi_b, win_a, win_b = get_predictions(
            df_players.copy(), df_stadiums.copy(), team_a, captain_a, team_b, captain_b, venue
        )

    return render_template(
        "index.html",
        teams=teams,
        venues=venues,
        players_by_team=players_by_team,
        xi_a=xi_a,
        xi_b=xi_b,
        team_a=team_a,
        team_b=team_b,
        venue=venue,
        win_a=win_a,
        win_b=win_b
    )

# multiple lineups
@app.route("/shuffle", methods=["POST"])
def shuffle():
    team_a = request.form["team_a"]
    captain_a = request.form["captain_a"]
    team_b = request.form["team_b"]
    captain_b = request.form["captain_b"]
    venue = request.form["venue"]

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

    xi_a = generate_shuffled_xi(df_players.copy(), team_a, captain_a, pitch_type, bowling_type, batting_bias, bowling_bias)
    xi_b = generate_shuffled_xi(df_players.copy(), team_b, captain_b, pitch_type, bowling_type, batting_bias, bowling_bias)

    score_a = sum(player['FitScore'] for player in xi_a)
    score_b = sum(player['FitScore'] for player in xi_b)
    win_a, win_b = simulate_win_percentage(score_a, score_b)

    return render_template(
        "index.html",
        teams=teams,
        venues=venues,
        players_by_team=players_by_team,
        xi_a=xi_a,
        xi_b=xi_b,
        team_a=team_a,
        team_b=team_b,
        venue=venue,
        win_a=win_a,
        win_b=win_b
    )

if __name__ == "__main__":
    app.run(debug=True)

