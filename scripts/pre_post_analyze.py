# A simple script to generate fake data
import datetime as dt
import json
import math
import random
import re
import sys

def rank_to_rating(rank):
    """Convert a rank string to a numerical rating."""
    if rank.endswith("p"):
        raise ValueError("P ranks should be set to 7d before getting here")
        #return 7.5
    elif rank.endswith("d"):
        return int(rank[:-1]) + 0.5
    elif rank.endswith("k"):
        return -int(rank[:-1]) - 0.5
    else:
        return -30

def get_player_by_id(player_id, json_data):
    """Get player by member ID."""
    pre_p = next((p for p in json_data if p["model"] == "agagd_core.players" and p["pk"] == player_id), None)
    return pre_p

def get_tournament_by_id(tournament_id, json_data):
    """Get tournament by ID."""
    return next((t for t in json_data if t["model"] == "agagd_core.tournament" and t["pk"] == tournament_id), None)

def get_games_by_player(player_id, json_data):
    """Get all games played by a player."""
    return [g for g in json_data if g["model"] == "agagd_core.game" and (g["fields"]["pin_player_1"] == player_id or g["fields"]["pin_player_2"] == player_id)]

def get_handicap(game):
    """Get handicap from a game."""
    if game["fields"]["handicap"] == 0 and game["fields"]["komi"] == 0:
        return 1
    return game["fields"]["handicap"]

def pretty_float(text, precision=2, space=5):
    """Convert text to float with specified precision."""
    try:
        v = round(float(text), precision)
        return f"{v:<5f}"
    except ValueError:
        return None

def close_kyu_dan_boundary(rating):
    if rating > 0:
        return rating - 1.0
    else:
        return rating + 1.0

def open_kyu_dan_boundary(rating):
    if rating > 0:
        return rating + 1.0
    else:
        return rating - 1.0

def get_declared_rating(pre_rating, declared_rank):
    """Calculate declared rating based on pre-rating and declared rank."""    
    pre_rating = float(pre_rating) # In case it's still a string
    declared_rating = rank_to_rating(declared_rank)
    declared_rating = close_kyu_dan_boundary(declared_rating)
    pre_rating = close_kyu_dan_boundary(pre_rating)
    deltaR = declared_rating - pre_rating
    if deltaR > 3.0:
        declared_rating = declared_rating # Trust large self promotions
    elif deltaR >= 1.0:
        declared_rating = pre_rating + 0.024746 + 0.32127 * deltaR  # Half-trust medium self promotions
    else:
        declared_rating = pre_rating # Ignore small self promotions
    declared_rating = open_kyu_dan_boundary(declared_rating)
    return declared_rating

def main():
    print("<pre>")
    USAGE = "Usage: python pre_post_analyze.py [pre.json] [post.json]"

    if len(sys.argv) < 2:
        print(USAGE)
        quit()
    try:
        pre_json_fn = sys.argv[1]
        post_json_fn = sys.argv[2]
    except ValueError:
        print(USAGE)
        quit()

    pre_json_data = json.load(open(pre_json_fn, encoding="utf-8"))
    post_json_data = json.load(open(post_json_fn, encoding="utf-8"))
    player_keys = set()
    for g in pre_json_data:
        if g["model"] == "agagd_core.game":
            player_keys.add(int(g["fields"]["pin_player_1"]))
            player_keys.add(int(g["fields"]["pin_player_2"]))

    print(f'For each player, each row is a different game with these columns:')
    print(f'oppid: Opponent\'s AGA ID')
    print(f'result: +/- for win or loss, my color, handicap')
    print(f'pre: Opp Rating before event')
    print(f"dec: Opponent's declared rank")
    print(f"dur: Opponent's effective starting rating, based on pre-rating and declared rank")
    print(f"post: Opponent's final rating after the event")
    print(f"tourney: Tournament this game is part of")
    print()
    
    for pk in sorted(player_keys):
        player = get_player_by_id(pk, pre_json_data)
        player_post = get_player_by_id(pk, post_json_data)
        games = get_games_by_player(pk, pre_json_data)
        print(f'Summary of games played by player AGAID: {player["pk"]:4d} ' +
              f'pre: {player["fields"]["rating"]} {player["fields"]["sigma"]} {player["fields"]["elab_date"]} ' +
              f'post: {player_post["fields"]["rating"]} {player_post["fields"]["sigma"]} {player_post["fields"]["elab_date"]}')
        print('              ---pre----    declared   ---post---           ')
        print('oppid result   R    sig     rating       R    sig     tourney')
        for game in games:
            if game["fields"]["pin_player_1"] == pk:
                opp_id = game["fields"]["pin_player_2"]
                color = "W"
                mypin = 1
                opppin = 2
            else:
                opp_id = game["fields"]["pin_player_1"]
                color = "B"
                mypin = 2
                opppin = 1
            player_result = "+" if game["fields"]["result"] == color else "-"
            opp_player = get_player_by_id(opp_id, pre_json_data)
            opp_player_post = get_player_by_id(opp_id, post_json_data)
            # print(opp_player)
            # print(game)
            tournament = get_tournament_by_id(game["fields"]["tournament_code"], pre_json_data)
            declared_rating = get_declared_rating(opp_player['fields']['rating'], game['fields'][f'rank_{opppin}'])
            print(
                f"{opp_player['pk']:5d} " +
                f"{player_result} {color} H{get_handicap(game)} " + 
                f"{opp_player['fields']['rating']:5.2f} {opp_player['fields']['sigma']:5.2f} " +
                f"| {game['fields'][f'rank_{opppin}']:>3s} " +
                f"{declared_rating:5.2f} " +
                f"| {opp_player_post['fields']['rating']:5.2f} {opp_player_post['fields']['sigma']:5.2f} " +
                f"| {tournament['fields']['description']}" +
                ""
            )
        print()
        

if __name__ == "__main__":
    main()

#            {
#                "pk": member_id,
#                "model": "agagd_core.players",
#                "fields": {
#                    "elab_date": join_date.strftime("%Y-%m-%d"),
#                    "name": given_names,
#                    "last_name": family_name,
#                    "rating": rating,
#                    "sigma": sigma,
#                },
#            }


# "model": "agagd_core.game",
#     "fields": {
#         "pin_player_1": int(parts[0]),
#         "pin_player_2": int(parts[1]),
#         "color_1": "W",
#         "color_2": "B",
#         "result": parts[2].upper(),
#         "handicap": int(parts[3]),
#         "elab_date": tournament["fields"]["elab_date"],
#         "tournament_code": tourny_id,
#         "sgf_code": "",
#         "komi": int(parts[4]),
#         "game_date": tournament["fields"]["elab_date"],
#         "round": rounds,
#         "rated": 0,
#         "online": 0,
#         "exclude": 0,
#         "rank_1": t_players[int(parts[0])]["rank"],
#         "rank_2": t_players[int(parts[1])]["rank"],
#     }
# }

