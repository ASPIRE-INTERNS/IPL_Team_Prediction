# core/utils.py

def simulate_win_percentage(score_a, score_b):
    """
    Calculate the win probability of Team A and Team B
    based on their total FitScores.

    Returns:
        (win_a_percent, win_b_percent)
    """
    total = score_a + score_b
    if total == 0:
        return 50.0, 50.0  # Neutral if no data

    win_a = (score_a / total) * 100
    win_b = 100 - win_a

    return round(win_a, 2), round(win_b, 2)
