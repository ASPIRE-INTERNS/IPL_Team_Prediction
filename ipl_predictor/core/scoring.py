# core/scoring.py
import math

def calculate_batting_score(row, batting_bias):
    try:
        inns = float(row.get('T20s - Batting - Inns', 1))
        eff = float(row['T20s - Batting - Ave']) + float(row['T20s - Batting - SR']) / 2
        return eff * math.log(inns + 1) * batting_bias
    except:
        return 0

def calculate_bowling_score(row, bowling_bias):
    try:
        inns = float(row.get('T20s - Bowling - Inns', 1))
        eff = (50 / (float(row['T20s - Bowling - Ave']) + 1)) + \
              (50 / (float(row['T20s - Bowling - Econ']) + 1)) + \
              (50 / (float(row['T20s - Bowling - SR']) + 1))
        return eff * math.log(inns + 1) * bowling_bias
    except:
        return 0

def calculate_fit_score(row, pitch_type, bowling_type, batting_bias, bowling_bias):
    bat_score = calculate_batting_score(row, batting_bias)
    bowl_score = calculate_bowling_score(row, bowling_bias)

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
