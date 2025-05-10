import json
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

with open('cokeShakeyTeam.json', 'r', encoding='utf-8') as f:
    team_data = json.load(f)

Smug = next(player["accounts"] for player in team_data["main_team"] if player["name"] == "Smug")
FDGood = next(player["accounts"] for player in team_data["main_team"] if player["name"] == "FDGood")
Uvabu = next(player["accounts"] for player in team_data["main_team"] if player["name"] == "Uvabu")

Bobou = next(player["accounts"] for player in team_data["sub_team"] if player["name"] == "Bobou")

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

def get_highest_account(player_accounts: list) -> str:
    # Get the account with the highest MMR for a list of player names
    current_mmr = -1
    highest_account = None

    for account_name in player_accounts:
        checking_mmr = get_user_rank(account_name)
        if current_mmr < checking_mmr:
            current_mmr = checking_mmr
            highest_account = account_name
    return highest_account

