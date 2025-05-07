import requests
import time
import os
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry


# API key and base URL for the API
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = 'https://open-api.bser.io/v1'
seasonId = 31  # Season 15
matchingTeamMode = 3  # Squads

# Lists of player names
Smug = ["SmugDragon", "HuntMeNadine"]
FDGood = ["FDGood"]
Uvabu = ["Uvabu", "Getcha", "ohmahgah"]
Bobou = ["팀워크와영광", "GuiltyChallenger"]

# Create a session to persist certain parameters across requests
session = requests.Session()
session.headers.update({'x-api-key': API_KEY})

# Rate limit: 1 request per second, 2 requests in a burst
@sleep_and_retry
@limits(calls=2, period=1)
def rate_limited_request(url, params=None):
    # Make a rate-limited request
    return session.get(url, params=params)

def get_ER_data(endpoint: str, params: dict = None, retries: int = 5) -> dict:
    # Construct the full URL
    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(retries):
        # Make a rate-limited request
        response = rate_limited_request(url, params)
        if response.status_code == 200:
            # Return the JSON response if successful
            return response.json()
        elif response.status_code == 429:
            # Handle rate limit exceeded error with exponential backoff
            print(f"Rate limit exceeded. Retrying in {2 ** attempt} seconds...")
            time.sleep(2 ** attempt)
        else:
            # Raise an error for other status codes
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()
    # Raise an exception if max retries are exceeded
    raise Exception("Max retries exceeded")

def get_user_number(player_name: str) -> int:
    # Get the user number for a given player name
    user_info = get_ER_data('user/nickname', {'query': player_name})
    user_num = user_info['user']['userNum']
    return user_num

def get_user_rank(player_name: str, matchingTeamMode: int = matchingTeamMode, seasonId: int = seasonId) -> int:
    # Get the user rank (MMR) for a given player name
    user_info = get_ER_data(f'rank/{get_user_number(player_name)}/{seasonId}/{matchingTeamMode}')
    user_mmr = user_info['userRank']['mmr']
    return user_mmr

def get_highest_account(player: list) -> str:
    # Get the account with the highest MMR for a list of player names
    current_mmr = -1
    highest_account = None

    for account_name in player:
        checking_mmr = get_user_rank(account_name)
        if current_mmr < checking_mmr:
            current_mmr = checking_mmr
            highest_account = account_name
    return highest_account

def team_ranking(Team: dict) -> dict:
    team_ranking = {}

    for key, players in Team.items():
        team_ranking[key] = {}
        for player in players:
            player_mmr = get_user_rank(player)
            team_ranking[key][player] = player_mmr
    return team_ranking

def get_team_average(Team: dict) -> dict:
    # Calculate the average MMR for a team
    team_mmr = {}
    total_mmr = 0
    count = 0

    for key, players in Team.items():
        highest_account = get_highest_account(players)
        highest_mmr = get_user_rank(highest_account)
        team_mmr[key] = {'account': highest_account, 'mmr': highest_mmr}
        total_mmr += highest_mmr
        count += 1

    team_mmr['average_mmr'] = round(total_mmr / count, 2) if count > 0 else 0
    return team_mmr

if __name__ == "__main__":
    # Define the teams
    Team = {1: Smug, 2: FDGood, 3: Uvabu}

    # Calculate and print the team ranking
    team_ranking_result = team_ranking(Team)
    print("Team Ranking:")
    for team, players in team_ranking_result.items():
        print(f"Team {team}:")
        for player, mmr in players.items():
            print(f"  {player}: {mmr}")
