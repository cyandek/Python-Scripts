# Script to download TV Show poster, background, season posters, and episode titlecards from Mediux based on last updated folder in directory

from urllib import response
import PTN
import time
import os, glob, logging
from datetime import datetime
import pytz
from imdbinfo import search_title, get_movie, get_name, get_season_episodes, get_reviews
import asyncio
from themoviedb import aioTMDb
import requests
import config

# Variable declarations ______________________________________________________________________________________________
movie_folder = "/mnt/nas/media/Movies"
tv_folder = "/mnt/nas/media/TV Shows"
ep_list = [] #list of episode files in folder
jpg_list = [] #list of jpg files in folder
ep_dict = {} #dictionary of episode files in folder with season and episode number
jpg_dict = {} #dict of jpg files in folder

# File logging config
logging.basicConfig(format='%(levelname)s:%(message)s', filename='/home/cyandek/projects/media/posters/posters.log', encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the timezone object
cst_now = pytz.timezone('America/Chicago') 

# Get the current time
datetime_now = datetime.now(cst_now).strftime('%m-%d-%Y %I:%M:%S')

# ________________________________________________________________________________________________________________________
# Function to get last edited folder from NAS
def get_nas_folder():

    # Find latest folder edited
    search_folder = max(glob.glob(os.path.join(tv_folder, '*')), key=os.path.getmtime)
    latest_folder = search_folder.replace("/mnt/nas/media/TV Shows/","")
    folder_tile = latest_folder.replace("/","")

    # Parse the title and year from the folder name
    folder_dict = PTN.parse(folder_tile)

    # Add search folder to dictionary
    folder_dict["folder"] = search_folder

    title = folder_dict["title"]
    year = folder_dict["year"]

    return folder_dict

# ________________________________________________________________________________________________________________________
def get_tv_poster():
    folder_dict = get_nas_folder()
    search_folder = folder_dict["folder"]
    title = folder_dict["title"]
    year = folder_dict["year"]

    existing_poster = False
    existing_fanart = False

    search_title = f'{title} {year}'
    logger.info(f"{datetime_now} - search_title: {search_title}")

    # Check if a poster already exists in folder
    file_list = os.listdir(search_folder)

    # Loop through files in folder and create lists/dictionaries
    for file in file_list:
        file_dict = PTN.parse(file)

        filename, file_extension = os.path.splitext(file)
        
        # Add jpg file names to list and dictionary
        if file_extension in ('.jpg', '.jpeg', '.png'):
            jpg_list.append(filename)

            try:
                jpg_dict[filename] = {
                    'season': file_dict['season'],
                    'episode': file_dict['episode']
                }
            except KeyError:
                logger.warning(f"{datetime_now} - Could not parse season/episode from file: {file}")  

        # Add episode file names to list and dictionary
        if file_extension in ('.mkv', '.mp4', '.avi', '.mov'):
            ep_list.append(filename)

            try:
                ep_dict[filename] = {
                    'season': file_dict['season'],
                    'episode': file_dict['episode']
                }
            except KeyError:
                logger.warning(f"{datetime_now} - Could not parse season/episode from episode file: {file}")



        if file == 'poster.jpg':
            existing_poster = True
            logger.info(f"{datetime_now} - There is already a poster downloaded for this show")

        if file == 'fanart.jpg':
            existing_fanart = True
            logger.info(f"{datetime_now} - There is already a fanart downloaded for this show")

    # Log jpg_dict for debugging
    #logger.info(f"{datetime_now} - jpg_dict: {jpg_dict}")
    #logger.info(f"{datetime_now} - jpg_list: {jpg_list}")

    # Compare episode list to jpg list to determine if any are missing
    missing_jpg_dict = {} #dictionary of episode files that are missing a titlecard with season and episode number
    for ep in ep_list:
        if ep not in jpg_list:
            try:
                missing_jpg_dict[ep] = {
                    'season': ep_dict[ep]['season'],
                    'episode': ep_dict[ep]['episode']
                }
            except KeyError:
                logger.warning(f"{datetime_now} - Could not add missing jpg for episode: {ep}")
    
    # Create copy of missing jpg dictionary to iterate through for renaming process
    missing_jpg_dict_copy = missing_jpg_dict.copy()

    # Compare missing jpg dictionary to episode dictionary for season and episode matches and rename jpg file to match episode file
    for ep in missing_jpg_dict:
        for jpg in jpg_dict:
            if missing_jpg_dict[ep]['season'] == jpg_dict[jpg]['season'] and missing_jpg_dict[ep]['episode'] == jpg_dict[jpg]['episode']:
                # Rename jpg file to match episode file
                old_jpg = f"{search_folder}/{jpg}.jpg"
                new_jpg = f"{search_folder}/{ep}.jpg"
                os.rename(old_jpg, new_jpg)
                logger.info(f"{datetime_now} - Renamed {old_jpg} to {new_jpg}")

                # Remove episode from missing jpg dictionary
                del missing_jpg_dict_copy[ep]

                break

    # Log missing or incorrectly named titlecard
    logger.info(f"{datetime_now} - Missing or incorrectly named Titlecard: {list(missing_jpg_dict.keys())}")

    # Update missing jpg dictionary after renaming process
    missing_jpg_dict = missing_jpg_dict_copy

    # Log updated list of missing jpg files after renaming process
    logger.info(f"{datetime_now} - Missing Titlecard after renaming: {missing_jpg_dict}")

    # API request to get Show ID based on title and year from folder name
    show_ID = tmdb_API_Request()
    logger.info(f"{datetime_now} - Show ID: {show_ID}")

    #search missing media
    
    mediux_base_url = "https://mediux.pro/shows/"
    mediux_URL ='https://images.mediux.io/graphql'

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Mozilla/5.0",
        "X-Request": "username",
        "Authorization": f"Bearer {config.mediux_API_KEY}"
    }

# Data for GraphQL query to get show information based on show ID
    data_by_showid = {
        "query": 
        f"""{{shows_by_id(id: {show_ID}) {{
                id 
                date_updated
                poster_path
                backdrop_path
                posters {{
                    id
                    modified_on
                    src
                    blurhash
                    show_set {{
                        id
                        user_created {{
                            username
                        }}
                        date_created
                        date_updated
                    }}
                }}
                backdrops {{
                    id
                    modified_on
                    src
                    blurhash
                    show_set {{
                        id
                        user_created {{
                            username
                        }}
                        date_created
                        date_updated
                    }}
                }}
                seasons {{
                    season_number
                    posters {{
                        id
                        modified_on
                        src
                        blurhash
                        show_set {{
                            id
                            user_created {{
                                username
                            }}
                            date_created
                            date_updated
                        }}
                    }}
                }}
                episodes {{
                    episode_title
                    episode_number
                    season_id {{
					    season_number
				    }}
                    titlecards {{
                        id
                        modified_on
                        src
                        blurhash
                        show_set {{
                            id
                            user_created {{
                                username
                            }}
                            date_created
                            date_updated
                        }}
                    }}
                }}
            }}
            }}
        """
    }
    
    logger.info(f"{datetime_now} - data_by_showid: {data_by_showid}")

    response = requests.post(mediux_URL, json=data_by_showid, headers=headers)
    logger.info(f"{datetime_now} - Response: {response.status_code} {response.text}")

    response_json = response.json()

    preferred_poster = False
    poster_src = None

    # Extract set ID and poster source by willtong93 user from response_json
    logger.info(f"{datetime_now} - Searching for poster by willtong93")
    for poster in response_json['data']['shows_by_id']['posters']:
        if poster['show_set']['user_created']['username'] == 'willtong93':
            show_set_id = poster['show_set']['id']
            poster_src = poster['src']

            logger.info(f"{datetime_now} - Found set ID: {show_set_id} for username: willtong93")
            preferred_poster = True
            logger.info(f"{datetime_now} - preferred_poster {preferred_poster}")
            break

    logger.info(f"{datetime_now} - preferred_poster {preferred_poster}")

    preferred_fanart = False
    fanart_src = None
    # Get fanart source by willtong93
    logger.info(f"{datetime_now} - Searching for fanart by willtong93")
    for backdrops in response_json['data']['shows_by_id']['backdrops']:
        if backdrops['show_set']['user_created']['username'] == 'willtong93':
            show_set_id = backdrops['show_set']['id']
            fanart_src = backdrops['src']

            logger.info(f"{datetime_now} - Found set ID: {show_set_id} for username: willtong93")
            preferred_fanart = True
            logger.info(f"{datetime_now} - preferred_fanart {preferred_fanart}")
            break
        else:
            try:
                fanart_src = response_json['data']['shows_by_id']['backdrops'][0]['src']
                logger.info(f"{datetime_now} - No fanart found by willtong. Fanart Src: {fanart_src}")
            except (KeyError, IndexError) as e:
                logger.warning(f"{datetime_now} - Error retrieving default fanart: {e}")
                fanart_src = None


    logger.info(f"{datetime_now} - preferred_fanart {preferred_fanart}")

    # If no set ID by willtong93 user is found, use the first set ID in the response_json
    if preferred_poster == False:
        try:
            show_set_id = response_json['data']['shows_by_id']['posters'][0]['show_set']['id']
            poster_src = response_json['data']['shows_by_id']['posters'][0]['src']

            logger.info(f"{datetime_now} - No set ID found for username: willtong93. Using first set: {show_set_id}")
            logger.info(f"{datetime_now} - No poster found by willtong. Poster Src: {poster_src}")
        except (KeyError, IndexError) as e:
            logger.warning(f"{datetime_now} - Error retrieving default poster: {e}")
            poster_src = None

    # Download poster if it does not already exist in folder
    if existing_poster == False:
        poster_output =f'{search_folder}/poster.jpg'
        logger.info(f"{datetime_now} - There is not a poster downloaded for this show")

        if poster_src is not None:
            poster_url = requests.get(f"https://api.mediux.pro/assets/{poster_src}")
            with open(poster_output, 'wb') as f:
                f.write(poster_url.content)

        logger.info(f"{datetime_now} - Poster downloaded to: {poster_output}")

    # Download fanart if it does not already exist in folder
    if existing_fanart == False:
        fanart_output =f'{search_folder}/fanart.jpg'
        logger.info(f"{datetime_now} - There is not a fanart downloaded for this show")

        if fanart_src is not None:
            fanart_url = requests.get(f"https://api.mediux.pro/assets/{fanart_src}")
            with open(fanart_output, 'wb') as f:
                f.write(fanart_url.content)

        logger.info(f"{datetime_now} - Downloading fanart to: {fanart_output}")
        

    season_set = set() #Set of season numbers
    season_posters = {} #Dict of season posters {name: {status:missing, src: url}}}
    
    #Determine number of seasons
    for ep in ep_dict:
        try:
            season_set.add(ep_dict[ep]['season'])
        except KeyError:
            logger.warning(f"{datetime_now} - No season found for episode {ep}")

    logger.info(f"{datetime_now} - List of seasons: {season_set}")

    number_of_seasons = max(season_set)
    logger.info(f"{datetime_now} - Number of seasons: {number_of_seasons}")

    # Create disctionary for season posters with status and source
    for season in range(1, number_of_seasons + 1):
        if season < 10:
            season_poster_name = f"season0{season}-poster"
            season_posters[season_poster_name] = {"season": season, "status": "missing", "src": None}
        else:
            season_poster_name = f"season{season}-poster"
            season_posters[season_poster_name] = {"season": season, "status": "missing", "src": None}

    logger.info(f"{datetime_now} - Season posters: {season_posters}")

    # Loop through jpg dictionary to check if season posters already exist in folder and update season_posters dictionary with status
    for jpg in jpg_list:
        for season_poster in season_posters:
            if jpg == season_poster:
                season_posters[season_poster]['status'] = 'exists'
                logger.info(f"{datetime_now} - Found existing season poster: {jpg} for season: {season_posters[season_poster]}")

    logger.info(f"{datetime_now} - Updated Season posters: {season_posters}")

    preferred_season_poster = False

    # Loop through season_posters dictionary to determine if any season posters are missing and get poster source
    for season_poster_name in season_posters:
        if season_posters[season_poster_name]['status'] == 'missing':
            # Get missing season from dict
            missing_season_num = season_posters[season_poster_name]['season']

            # Loop through seasons in response_json to find missing season
            for season in response_json['data']['shows_by_id']['seasons']:
                if season['season_number'] == missing_season_num:

                    # Loop through posters in the missing season section of response_json to find one by willtong93
                    for poster in season['posters']:
                        if poster['show_set']['user_created']['username'] == 'willtong93':
                            logger.info(f"{datetime_now} - Found Season {missing_season_num} poster created by willtong93")
                            show_set_id = poster['show_set']['id']
                            season_src = poster['src']
                            preferred_season_poster = True
                            logger.info(f"{datetime_now} - Source for willtong93 season poster: {season_src}")
                            break
                        
                        else:
                            season_src = season['posters'][0]['src']  

                    logger.info(f"{datetime_now} - Season {missing_season_num} Preferred poster found: {preferred_season_poster}")
 
            # Download season poster
            try:
                season_poster_output =f'{search_folder}/{season_poster_name}.jpg'
                if season_src is not None:
                    season_poster_url = requests.get(f"https://api.mediux.pro/assets/{season_src}")
                    with open(season_poster_output, 'wb') as f:
                        f.write(season_poster_url.content)
            except Exception as e:
                logger.error(f"{datetime_now} - Error downloading season poster for season {missing_season_num}: {e}")

            logger.info(f"{datetime_now} - Downloading season poster for season {missing_season_num} to: {season_poster_output}")

    preferred_titlecard = False
    titlecard_src = None
    # Loop through missing dictionary to determine if any season posters are missing and get poster source
    for missing_titlecard in missing_jpg_dict:
            
        # Loop through episodes in response_json to find missing season
        for episode in response_json['data']['shows_by_id']['episodes']:
            if episode['season_id']['season_number'] == missing_jpg_dict[missing_titlecard]['season'] and episode['episode_number'] == missing_jpg_dict[missing_titlecard]['episode']:

                # Loop through titlecards in the missing episode section of response_json to find one by willtong93
                for titlecard in episode['titlecards']:
                    if titlecard['show_set']['user_created']['username'] == 'willtong93':
                        logger.info(f"{datetime_now} - Found titlecard for {missing_jpg_dict[missing_titlecard]} created by willtong93")
                        show_set_id = titlecard['show_set']['id']
                        titlecard_src = titlecard['src']
                        preferred_titlecard = True
                        logger.info(f"{datetime_now} - Source for willtong93 season poster: {titlecard_src}")
                        break
                    
                    else:
                        titlecard_src = episode['titlecards'][0]['src']  

                logger.info(f"{datetime_now} - Preferred titlecard found for {missing_jpg_dict[missing_titlecard]}: {preferred_titlecard}")

        # Download titlecard
        try:
            titlecard_output =f'{search_folder}/{missing_titlecard}.jpg'
            if titlecard_src is not None:
                titlecard_url = requests.get(f"https://api.mediux.pro/assets/{titlecard_src}")
                with open(titlecard_output, 'wb') as f:
                    f.write(titlecard_url.content)
                logger.info(f"{datetime_now} - Downloading titlecard for season {missing_jpg_dict[missing_titlecard]['season']} episode {missing_jpg_dict[missing_titlecard]['episode']} to: {titlecard_output}")
        except Exception as e:
            logger.error(f"{datetime_now} - Error downloading titlecard for season {missing_jpg_dict[missing_titlecard]['season']} episode {missing_jpg_dict[missing_titlecard]['episode']}: {e}")

# ________________________________________________________________________________________________________________________
def tmdb_API_Request():
    logger.info(f"{datetime_now} - Starting tmdb_API_Request()")

    folder_dict = get_nas_folder()
    title = folder_dict["title"]
    year = folder_dict["year"]

    logger.info(f"{datetime_now} - Title: {title}")
    logger.info(f"{datetime_now} - Year: {year}")

    try:
        url = f"https://api.themoviedb.org/3/search/tv?query={title}&first_air_date_year={year}&include_adult=true&language=en-US&page=1"

        headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {config.moviedb_API_KEY}"
        }

        response = requests.get(url, headers=headers)
        logger.info(f"{datetime_now} - Response Text: {response.text}")

        response_json = response.json()
        show_id = response_json['results'][0]['id']

        logger.info(f"{datetime_now} - Show ID: {show_id}")

    except Exception as e:
        logger.error(f"{datetime_now} - Error in tmdb_API_Request(): {e}")  
    
    return show_id
  
# _________________________________________________________________________________________________________________________
# Main script execution 
datetime_now = datetime.now(cst_now).strftime('%m-%d-%Y %I:%M:%S')

logger.info(f"{datetime_now} - calling get_tv_poster()")
get_tv_poster()
