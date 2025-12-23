# Import libraries ___________________________________________________________________________________________________
from plexapi.server import PlexServer
import config

# Variable declarations ______________________________________________________________________________________________
plex = PlexServer(config.server_ip, config.plex_token)

# Library variables
shows = plex.library.section('TV Shows')
movies = plex.library.section('Movies')
documentaries = plex.library.section('Documentaries')
cartoons = plex.library.section('Cartoons')
music = plex.library.section('Music')

# Input titles
input_show = "Friends"
input_movie = "Interstellar"
input_doc = "Bye Bye Barry"
input_cartoon = "SpongeBob SquarePants"

num_seasons = 0
num_episodes = 0


# List all unwatched TV Shows.
def unwatched_shows(shows):
    for show in shows.search(unwatched=True):
        print(show.title)

# List all unwatched Movies.
def unwatched_movies(movies):
    for movie in movies.search(unwatched=True):
        print(movie.title)

# List all unwatched Documentaries.
def unwatched_docs(documentaries):
    for doc in documentaries.search(unwatched=True):
        print(doc.title)

# List all unwatched Cartoons.
def unwatched_cartoons(cartoons):
    for cartoon in cartoons.search(unwatched=True):
        print(cartoon.title)

# Mark as played.
def mark_played(input_show):
    plex.library.section('TV Shows').get(input_show).markPlayed()


# Fetch audio and subtitle streams for the first episode
def streams(shows,input_show):
    episode = shows.get(input_show).episodes()[0]
    episode.reload()
    episodePart = episode.media[0].parts[0]
    audioStreams = episodePart.audioStreams()
    subtitleStreams = episodePart.subtitleStreams()
    print(f"Episode: {episode.title}")
    print(f"Audio Streams: {audioStreams}")
    print(f"Subtitle Streams: {subtitleStreams}")

# Fetch number of seasons and episodes for a specific TV show
def S_E_count(shows, input_show):
    show = shows.get(input_show)
    num_seasons = len(show.seasons())
    num_episodes = len(show.episodes())
    print(f"Number of seasons: {num_seasons}")
    print(f"Number of episodes: {num_episodes}")
    SE_list = [num_seasons,num_episodes]
    return SE_list


#Loop through all episodes and turn off the subtitles
def subtitles_off(input_show, num_episodes):
    for x in range(num_episodes):
        input_show.episodes()[x].media[0].parts[0].setSelectedSubtitleStream(0)
        input_show.episodes()[x].reload()
        print(x)

#List all episode titles in Season 1
def list_ep(shows, input_show, SE_list):
    num_seasons = SE_list[0]
    num_episodes = SE_list[1]
    for e in range(num_episodes):
        print(f"S{s}E{e}: {shows.get(input_show).seasons()[0].episodes()[e].title}")
                              

if __name__ == "__main__":

    unwatched_shows(shows)
    unwatched_movies(movies)
    unwatched_docs(documentaries)
    unwatched_cartoons(cartoons)
    mark_played(input_show) 
    streams(shows,input_show)
    S_E_count(shows, input_show)
    subtitles_off(input_show, num_episodes)
    list_ep(shows, input_show, S_E_count(shows, input_show))
