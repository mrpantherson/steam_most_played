# steam_most_played

This script retrieves a user's information from steam and saves it to a CSV, optionally it
can produce some visualizations based on this data.  The user's account must be set to 
public or it will not be able to be accessed,  you will also need to request a steam
API key.

# usage

This would collect information from STEAM_USER_ID with no viz

py steam_played.py API_KEY STEAM_USER_ID -v

This would use a locally saved copy of the data to generage a viz

py steam_played.py API_KEY STEAM_USER_ID -d
