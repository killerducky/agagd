import sys

# Process tournament report text file and set komi to 0 for handicap games.
# Usage: python clean_handicap_komi.py <input_file>

input_file = sys.argv[1]

games_section = False
with open(input_file, "r") as infile:
    for line in infile:
        if not games_section and not line.startswith("GAMES"): 
            print(line.strip())
            continue
        games_section = True
        parts = line.strip().split()
        if len(parts) == 5 and parts[3] != "0":
            parts[4] = "0"
        print("\t".join(parts))
