# A simple script to generate fake data
import datetime as dt
import json
import math
import random
import re
import sys

USAGE = "Usage: python parse_tdlist.py [tdlist_file] [tournament.txt]"

# Country Names and Codes
COUNTRY_NAMES = ["United States", "Canada", "Japan", "Korea", "China", "Tywain"]
COUNTRY_CODES = [
    "US",
    "CA",
    "JP",
    "KO",
    "CH",
    "TW",
]  # these, oddly, are not the FK in the member table.

# Membership Status Codes
STATUS_CODES = ["accepted"]

# Membership Types
MEMBERSHIP_TYPES = ["Full", "Sustainer", "Sponser", "Lifetime", "E-Journal"]

if len(sys.argv) < 2:
    print(USAGE)
    quit()
try:
    tdlist_fn = sys.argv[1]
    tournament_fns = sys.argv[2:]
except ValueError:
    print(USAGE)
    quit()

members = []
players = []
ratings = []

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

#Fields:
#Name, AGAID, Member Type, Rating, Expiration Date, Chapter Code, State, Sigma, Join Date
#Aarhus, Bob	9616	Full	-21.94000	1/1/2008	NOVA	VA	0.87000	11/1/2001
with open(tdlist_fn, encoding="utf-8") as f:
    for line in f:
        fields = line.strip().split("\t")
        #print (fields)
        try:
            name = fields[0]
            member_id = int(fields[1])
            member_type = fields[2]
            rating = float(fields[3])
            exp_date = dt.datetime.strptime(fields[4], "%m/%d/%Y").date()
            club = fields[5]
            state = fields[6]
            sigma = float(fields[7])
            join_date = dt.datetime.strptime(fields[8], "%m/%d/%Y").date()
            (family_name, given_names) = re.split(r'\s*,\s*', name)
        except:
            #print(f"Error processing line: {line.strip()}")
            continue

        members.append(
            {
                "pk": member_id,
                "model": "agagd_core.member",
                "fields": {
                    "member_id": member_id,
                    "legacy_id": member_id,  # Assuming legacy ID is same as member ID
                    "full_name": name,
                    "given_names": given_names,
                    "family_name": family_name,
                    "join_date": join_date.strftime("%Y-%m-%d"),
                    "renewal_due": exp_date.strftime("%Y-%m-%d"),
                    "city": "city",
                    "state": state,
                    "status": "accepted",
                    "region": "some region",
                    "country": "country",
                    "chapter": club,
                    "chapter_id": random.choice(range(1, 5)),  # Assuming chapter IDs are 1-4
                    "occupation": "",
                    "citizen": random.choice([0, 1]),
                    "password": "hallo!",
                    "type": member_type,
                    "last_changed": join_date.strftime("%Y-%m-%d" + "T00:00:00+00:00"), # I think Z would have worked too
                },
            }
        )
        players.append(
            {
                "pk": member_id,
                "model": "agagd_core.players",
                "fields": {
                    "elab_date": join_date.strftime("%Y-%m-%d"),
                    "name": given_names,
                    "last_name": family_name,
                    "rating": rating,
                    "sigma": sigma,
                },
            }
        )
        ratings.append(
            {
                "pk": None,  # Rating ID is not specified, will be auto-generated
                "model": "agagd_core.rating",
                "fields": {
                    "pin_player": member_id,
                    "elab_date": join_date.strftime("%Y-%m-%d"),
                    "rating": rating,
                    "tournament": None,  # No tournament associated with this rating
                    "sigma": sigma,
                },
            }
        )

# TOURNAMENT 
# US Open Austin, Texas, July 13 2025 
# start=7/13/2025 
# finish=7/13/2025 
# rules=aga 
#
# PLAYERS 
# 31648   Jin, Weibin                7p 
# 22817   Zhang, Tianyuan            6d 
# 31678   Cho, Daehee                6d 
#
# GAMES 1 
# WHITE   BLACK   WINNER  HANDICAP KOMI
# 24545   13194 	 w	 0	 6 
# 15343   4146  	 b	 0	 6 
# END

tournaments = []
games = []

tourny_id = 0
game_id = 0
for tournament_fn in tournament_fns:
    tourny_id += 1
    tournament = {
        "pk": tourny_id,
        "model": "agagd_core.tournament",
        "fields": {
            "total_players": 0,
            "city": "city",
            "elab_date": "",
            "description": "",
            "wall_list": "",
            "state": "",
            "rounds": 0,
            "tournament_date": "",
        },
    }
    t_players = {}
    with open(tournament_fn, encoding="utf-8") as f:
        current_section = None
        rounds = 0
        for line in f:
            line = line.strip()
            if line == "": continue

            # Section headers
            if line.startswith("TOURN"):
                current_section = "tournament"
                if line.startswith("TOURNEY"):
                    tournament["fields"]["description"] = line[len("TOURNEY"):].strip() # Wow AI said do it this way. Well ok it works!
                continue
            elif line.startswith("PLAYERS"):
                current_section = "players"
                continue
            elif line.startswith("GAMES"):
                current_section = "games"
                rounds += 1
                continue
            elif line.startswith("END"):
                current_section = None
                break
            if current_section == "tournament":
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key == "start":
                        tournament["fields"]["elab_date"] = dt.datetime.strptime(val.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
                        tournament["fields"]["tournament_date"] = dt.datetime.strptime(val.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
                else:
                    tournament["fields"]["description"] = line
            elif current_section == "players":
                if line.startswith("#"): continue  # Skip comments -- should this be done for the other sections too?
                # Format: ID   Name               Rank
                m = re.match(r"(\d+)\s+(.*)\s+(\d+[pdk])", line)
                if m:
                    pid, name, rank = m.groups()
                    if rank.endswith("p"): 
                        raise ValueError("\n" + tournament_fn + "\n" + line + "\n" + "P ranks should be set manually")
                    # if rank.endswith("p"): rank = "7d"
                    pid = int(pid)
                    name = name.strip()
                    (family_name, given_names) = re.split(r'\s*,\s*', name)
                    t_players[int(pid)] = {
                        "name": name,
                        "rank": rank
                    }
                    tournament["fields"]["total_players"] += 1
                    # If player didn't exist in tdlist, create a new player entry
                    if not any(player["pk"] == pid for player in players):
                        (family_name, given_names) = re.split(r'\s*,\s*', name)
                        players.append(
                            {
                                "pk": pid,
                                "model": "agagd_core.players",
                                "fields": {
                                    "elab_date": tournament["fields"]["elab_date"], # TODO: How to handle new players?
                                    "name": given_names,
                                    "last_name": family_name,
                                    "rating": rank_to_rating(rank),
                                    "sigma": 0.5,  # Default for new players
                                },
                            }
                        )
                        members.append(
                            {
                                "pk": int(pid),
                                "model": "agagd_core.member",
                                "fields": {
                                    "member_id": pid,
                                    "legacy_id": pid,
                                    "full_name": name,
                                    "given_names": given_names,
                                    "family_name": family_name,
                                    "join_date": tournament["fields"]["elab_date"],
                                    "renewal_due": tournament["fields"]["tournament_date"],
                                    "city": "city",
                                    "state": "state",
                                    "status": "accepted",
                                    "region": "some region",
                                    "country": "country",
                                    "chapter": "",
                                    "chapter_id": 0,
                                    "occupation": "",
                                    "citizen": 1,
                                    "password": "hallo!",
                                    "type": "Full",
                                    "last_changed": tournament["fields"]["elab_date"] + "T00:00:00+00:00",
                                },
                            }
                        )
                else:
                    raise ValueError(f"Warning: Could not parse player line: {line}")
            elif current_section == "games":
                # Format: BlackID  WhiteID  Winner  Handicap  Komi
                #          24545     13194 	  w	       0       6 
                parts = line.split()
                # Skip forfeits / no result
                if len(parts) == 5 and parts[2] != "?":
                    game_id += 1
                    g = {
                        "pk": game_id,
                        "model": "agagd_core.game",
                        "fields": {
                            "pin_player_1": int(parts[0]),
                            "pin_player_2": int(parts[1]),
                            "color_1": "W",
                            "color_2": "B",
                            "result": parts[2].upper(),
                            "handicap": int(parts[3]),
                            "elab_date": tournament["fields"]["elab_date"],
                            "tournament_code": tourny_id,
                            "sgf_code": "",
                            "komi": int(parts[4]),
                            "game_date": tournament["fields"]["elab_date"],
                            "round": rounds,
                            "rated": 0,
                            "online": 0,
                            "exclude": 0,
                            "rank_1": t_players[int(parts[0])]["rank"],
                            "rank_2": t_players[int(parts[1])]["rank"],
                        }
                    }
                    g["fields"]["komi"] = 7 if g["fields"]["komi"] == 6 else g["fields"]["komi"]
                    if g["fields"]["komi"] != 0 and g["fields"]["komi"] != 7:
                        print(f"Warning: Invalid komi {g['fields']['komi']} in game {g}")
                        exit(1)
                    games.append(g)
    tournament["rounds"] = rounds
    tournaments.append(tournament)

print(
    json.dumps(
        members + players + ratings + tournaments + games,
        indent=4,
    )
)
