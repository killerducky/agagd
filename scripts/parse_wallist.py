# Convert wallist txt file to standard AGA tournament format
import json
import re
import sys


def main():
    # TODO: Next level crazy is to try something like difflib.get_close_matches
    aliases = {
        "Palacios Vela, Luis Jorge": "PALACIOS, LUIS J",
        "Salinas Trevino, Saul": "Salinas Treviño, Saúl",
        "Kintanar, Agusti": "Kintanar, Agustin",
    }

    USAGE = "Usage: python parse_wallist.py [tdlist.json] [wallist]"
    if len(sys.argv) < 3:
        print(USAGE)
        quit()
    try:
        json_fn = sys.argv[1]
        wallist_fn = sys.argv[2]
    except ValueError:
        print(USAGE)
        quit()

    with open(json_fn, encoding="utf-8") as f:
        tdlist = json.load(f)
        # print (json.dumps(tdlist, indent=2))
        # {'pk': 57, 'model': 'agagd_core.member', 'fields': {'member_id': 57, 'legacy_id': 57, 'full_name': 'Lash, Michael', 'given_names': 'Lash,', 'family_name': 'Michael', 'join_date': '2025-06-19', 'renewal_due': '2064-09-01', 'city': 'city', 'state': 'VA', 'status': 'accepted', 'region': 'some region', 'country': 'country', 'chapter': 'NOVA', 'chapter_id': 2, 'occupation': '', 'citizen': 0, 'password': 'hallo!', 'type': 'Life', 'last_changed': '2025-06-19T00:00:00+00:00'}}
        
    games_one_player = []   # temp store when we have only one player's info
    games_both_players = []  # move to here when we have both players' info
    min_pid = 0
    wallist_id_to_member = {}
    players = []
    with open(wallist_fn, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith("#"):
                print(line[1:])
            m = re.match(r"(\d+):\s+(.*)\s+(\d+[pdk])\s+(.*)", line)
            if not m: continue
            pid, name, rank, results = m.groups()
            pid = int(pid)
            if pid < min_pid:
                raise ValueError(f"PID {pid} is greater than max PID {max_pid} found so far.")
            min_pid = pid
            name = name.strip()
            if name in aliases:
                name = aliases[name]
            results = results.strip().split()[:-1]  # Exclude the last item which is the score
            member = next((x for x in tdlist if x["model"] == "agagd_core.member" and x["fields"]["full_name"].lower() == name.lower()), None)
            wallist_id_to_member[pid] = member
            if not member:
                raise ValueError(f"Member {name} not found in tdlist.json")
            players.append(f'{member["fields"]["member_id"]:<7} {name:<30} {rank:<3}')
            for result in results:
                if result == "bye": continue
                m = re.match(r"(\d+)([+-])/([bw])(\d*)", result)
                if not m:
                    raise ValueError(f"Could not parse result: {result} in line: {line}")
                oppid, winner, color, handicap = m.groups()
                winner = color if winner == "+" else ("b" if color == "w" else "w")
                oppid = int(oppid)
                handicap = int(handicap)
                key = (pid, oppid) if color == "w" else (oppid, pid)
                if oppid > pid:
                    games_one_player.append({
                        "key": key,
                        "winner": winner,
                        "handicap": handicap,
                        "komi": 7,
                    })
                else:
                    game = next((x for x in games_one_player if x["key"] == key), None)
                    if not game:
                        raise ValueError(f"Matching game not found for key {key}.")
                    if not game["winner"] == winner:
                        raise ValueError(f"Winner mismatch for game {key}: expected {game['winner']}, got {winner}.")
                    games_one_player.remove(game)
                    if color == "b":
                    # Only the black player has the handicap, overwrite.
                        game["handicap"] = handicap
                    games_both_players.append(game)

    print("")
    print("PLAYERS")
    for p in players: print(p)

    if games_one_player:
        for game in games_one_player:
            white_id, black_id = game["key"]
            white_member = wallist_id_to_member.get(white_id)
            black_member = wallist_id_to_member.get(black_id)
            print(f"Error: white #{white_id:3} {white_member['fields']['full_name']:<20} {white_member['fields']['member_id']:<6} and " +
                         f"black #{black_id:3} {black_member['fields']['full_name']:<20} {black_member['fields']['member_id']:<6} not matched.")

        raise ValueError(f"Some games were not matched: {games_one_player}")

    print("")
    print("GAMES 1")
    for game in games_both_players:
        white_id, black_id = game["key"]
        white_id = wallist_id_to_member[white_id]['fields']['member_id']
        black_id = wallist_id_to_member[black_id]['fields']['member_id']
        print(f'{white_id:<7} {black_id:<7} {game["winner"]:<1} {game["handicap"]:>3} {game["komi"]:>3}')

if __name__ == "__main__":
    main()


#  17: Hansen, Erik Ryan            3k    44+/w0    45+/w0    39+/w0    23+/b2    42+/w0    22+/b0    24+/b2  7-0-0
#  18: Huang, Ryan                  2d     3-/b3       bye       bye       bye       bye       bye       bye  0-1-6
#  19: Zhou, Angel                  2d    14-/b0       bye       bye       bye       bye       bye       bye  0-1-6
#  20: Jauregui, Manny              1d       bye       bye       bye     9+/b1    28-/w0       bye       bye  1-1-5
#  21: Salinas Trevino, Saul        1d    30+/b0     9-/b0    23-/b0       bye       bye       bye       bye  1-2-4
#  22: Dahlin, Casey                3k    25-/b1    70+/w0    46+/w0    56+/w0    34+/b1    17-/w0    31+/b1  5-2-0
#  23: Robinson, Austin             1k     9-/b0    30+/w0    21+/w0    17-/w0    38-/w0       bye       bye  2-3-2
