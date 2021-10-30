import sys, os, re, subprocess
from ytmusicapi import YTMusic

genre_codes = {
	"NONE": "Unknown",
	"PDM": "Progressive Death Metal",
	"BM": "Black Metal",
	"TDM": "Technical Death Metal",
	"PM": "Progressive Metal",
	"SW": "Synthwave",
	"R": "Rock",
	"HR": "Hard Rock",
	"EM": "Extreme Metal",
	"MDM": "Melodic Death Metal",
	"HM": "Heavy Metal",
	"PR": "Progressive Rock",
	"MC": "Mathcore",
	"IM": "Industrial Metal",
	"I": "Industrial"
}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

PROMPT = f"{bcolors.BOLD}{bcolors.OKGREEN}YouMuPi>>> {bcolors.ENDC}{bcolors.ENDC}"
MUSIC_DIR = ""

"""
	Depends on:
		ytmusicapi
		yt-dlp
		kid3-cli
"""
def setup_dependencies():

	print("Installing ytmusicapi, yt-dlp, kid3-cli")

	os.system("pip3 install ytmusicapi")

	if hasattr(sys, 'getwindowsversion'):
		print(f"{bcolors.WARNING}Looks like you're a Windows user. You will need to manually install the following dependencies for now")
		print(f"  yt-dlp\thttps://github.com/yt-dlp/yt-dlp#release-files")
		print(f"  kid3-cli\thttps://kid3.kde.org/#download{bcolors.ENDC}")
		return

	os.system("sudo wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O /usr/local/bin/yt-dlp")
	os.system("sudo chmod a+rx /usr/local/bin/yt-dlp")

	os.system("sudo add-apt-repository ppa:ufleisch/kid3")
	os.system("sudo apt-get update")
	os.system("sudo apt-get install kid3-cli")

	print("Done adding dependencies")
	print("Restarting script...\n\n")

	os.execv(sys.executable, ["python3"]+sys.argv)

def print_genres():
	print()
	print("GENRE CODES")
	for k in genre_codes:
		print(k, "\t\t", genre_codes[k])
	print("If your genre is not listed, just provide your genre as it is. If you don't provide any genre, you will be prompted to once an album download is complete. So provide NONE as genre code in all your queries, for uninterrupted downloads")
	print()

def accept_genre():
	print("Enter the genre or genre code\n Enter h to view available genre codes")
	while True:
		genre = input(PROMPT)
		if genre == "h":
			print_genres()
		else: 
			return genre if genre not in genre_codes else genre_codes[genre]


def download_songs():
	print()
	print("Enter your download query keywords as\n command --parameter1 'value1' 'value2' --parameter2 'value1' 'value2' ...")
	print("Commands:\n Show genre codes: 'h'\n Exact song data is known: 'song'\n Choose from search results: 'surf'")
	print("Parameters:\n Song Name: '-t' \n Album Name - '-a'\n Artist Name - '-s'\n Year - '-y'\n Genre (or genre code) - '-g'\n Skip download confirmation - '-nc'\n Other keywords - '-k' (only for 'surf')")
	print(f"{bcolors.WARNING}Maximum two different values of same parameter type are allowed in case of 'surf' and maximum of one in case of 'song'{bcolors.ENDC} Extra will be ignored")
	print(f"{bcolors.WARNING}Maximum 10 words in the values are allowed in total{bcolors.ENDC}")
	print(f"{bcolors.FAIL}'$', '-' sign in any value is not allowed. Drop the $ sign or replace it{bcolors.ENDC}")

	queries = {"t":[], "a":[], "s":[], "y":[], "g":[], "k":[]}

	while True:
		query = input(PROMPT)

		if query == "h":
			print_genres()
			continue

		valid = True
		############### TOKENS ####################
		query_params = query.split(" -")
		for i in range(len(query_params)):
			param = query_params[i]
			param = param.strip()
			param = re.sub(r"'?\s'", r"$", param).rstrip("'").lstrip("-")
			param = param.split(r"$")
			query_params[i] = param

			if len(param) > 1: queries[param[0]] = param[1:]

		print(queries)

		if valid: break

		############### PARSE ####################


def download_album(album_data, artist=None, genre=None):

	album_playlist_id = album_data['audioPlaylistId']
	# In case user was wrong
	album = album_data['title']
	year = album_data['year']

	if artist is None:
		artist = album_data['artists'][0]['name']

	os.chdir(MUSIC_DIR)
	path = os.path.join(artist, album.replace("/", "_"))
	os.makedirs(path, exist_ok=True)
	os.chdir(path)

	print("Downloading...")
	os.system(f"yt-dlp -x --audio-format mp3 https://music.youtube.com/playlist?list={album_playlist_id}")
	print("Download complete!")

	print("Cleaning filenames and setting track tags...")
	audio_files = [file for file in os.listdir() if file.endswith(".mp3")]
	audio_files.sort(key = os.path.getctime)

	i = 1
	for file in audio_files:
		new_file = re.sub(" \\[[A-Za-z0-9_-]*\\]\\.mp3", ".mp3", file)
		os.rename(file, new_file)
		subprocess.call(['kid3-cli', '-c', f'select "{new_file}"', '-c', f'set title "{new_file.rstrip(".mp3").replace("_", "/")}"', '-c', f'set "track number" {str(i)}', '-c', 'save', '-c', 'select none'])
		i = i+1

	print("Setting common album tags...")
	if genre is None or genre == "": 
		genre = accept_genre()
	subprocess.call(['kid3-cli', '-c', 'select *.mp3', '-c', f'set artist "{artist}"', '-c', f'set album "{album}"', '-c', f'set genre "{genre}"', '-c', f'set date {year}', '-c', 'save', '-c', 'select none'])

	print(f"File setup done for {album} by {artist}")
	print()

def download_albums():
	print()
	print("Enter your download queries one by one in the form 'Album Name_Artist Name_Genre Code (or) Genre' (Genre field is optional)'\n Enter i to setup dependencies\n Enter d when done\n Enter h to show available genre codes\n Enter q to quit")
	queries = []
	while True:
		i = input(PROMPT)
		if i == "i":
			setup_dependencies()
		elif i == "d": 
			break
		elif i == "q":
			quit()
		elif i == "h":
			print_genres()
		else:
			queries.append(i)

	print()
	print("Queued " + str(len(queries)) + " albums to be downloaded. Proceed? (y for yes, any key for no)")
	confirm = input(PROMPT)

	if not confirm.lower() == 'y':
		print("User interrupt. Exiting...")
		quit()

	print()

	for query in queries:
		try:
			album, artist, genre = query.split("_")
			genre = genre if genre not in genre_codes else genre_codes[genre]
		except:
			try:
				album, artist = query.split("_")
				genre = None
			except:
				print("Bad input query: " + query + "\nSkipping...\n")
				continue

		results = ytmusic.search(query = album + " " + artist, filter = "albums")
		album_matches = [x for x in results if x['category'].lower() == 'albums' or x['category'].lower() == 'top results']

		if(len(album_matches) == 0):
			print(f"OOPS! Could not find {album} by {artist}. Ensure spelling is correct. Skipping...")
			print()
			continue

		best_result_data = album_matches[0]
		album_data = ytmusic.get_album(best_result_data['browseId'])

		download_album(album_data)

	print("All albums downloaded! Enjoy")


def download_discography():

	print()
	print("Enter your download queries one by one in the form 'Artist Name_Album Name_Genre Code (or) Genre' (Album and Genre fields are optional. They are used as keywords and nothing else)'\n Enter i to setup dependencies\n Enter d when done\n Enter h to show available genre codes\n Enter q to quit")
	print(f"{bcolors.FAIL}This utility does not infer genre of the albums unless a genre is provided, in which case it is applied to all albums{bcolors.ENDC}")
	queries = []
	while True:
		i = input(PROMPT)
		if i == "i":
			setup_dependencies()
		elif i == "d": 
			break
		elif i == "q":
			quit()
		elif i == "h":
			print_genres()
		else:
			queries.append(i)

	print()
	print("Queued " + str(len(queries)) + " artists to be downloaded. Proceed? (y for yes, any key for no)")
	confirm = input(PROMPT)

	if not confirm.lower() == 'y':
		print("User interrupt. Exiting...")
		quit()

	for query in queries:
		query_list = query.split("_")
		try:
			artist = query_list[0]
		except:
			print(f"Bad input query: {query}\nSkipping...\n")
			continue

		if len(query_list) > 2:
			genre = query_list[2] if genre not in genre_codes else genre_codes[query_list[2]]
		else:
			genre = None

		results = ytmusic.search(query = artist, filter = "artists")
		artist_matches = [x for x in results if x['category'].lower() == 'artists' or x['category'].lower() == 'top results']

		if(len(artist_matches) == 0):
			print(f"OOPS! Could not find {artist}. Ensure spelling is correct. Skipping...")
			print()
			continue

		best_result_data = artist_matches[0]
		# In case user was wrong
		artist = best_result_data['artist']

		artist_partial_data = ytmusic.get_artist(best_result_data['browseId'])

		try:
			params = artist_partial_data["albums"]["params"]
			browse = artist_partial_data["albums"]["browseId"]

			artist_discog = ytmusic.get_artist_albums(browse, params)
		except:
			artist_discog = artist_partial_data["albums"]["results"]

		print()
		print("Collected albums: ")
		i = 0
		for entry in artist_discog:
			print(f"  {i}.\t{entry['title']} -- {entry['year']}")
			i += 1
		print("Enter a space-separated list of numbers to specify albums to download, enter 'ALL' for all albums")
		s = input(PROMPT)
		if s == "ALL":
			choices = range(len(artist_discog))
		else:
			choices = re.sub(r"\s+", " ", s).split(" ")
		print()

		for selection in choices:
			try:
				entry = artist_discog[int(selection)]
			except:
				print(f"Invalid selection number {selection}. Skipping...")
				continue

			album_data = ytmusic.get_album(entry['browseId'])
			download_album(album_data, artist, genre)

	print(f"Selected albums by {artist} downloaded! Enjoy")



def main():

	global MUSIC_DIR

	print(f"{bcolors.HEADER}Welcome to YouMuPi!{bcolors.ENDC}\nThis is a work in progress and so far allows downloading albums by a simple query and tags the downloaded mp3 files automatically with:")
	print(" - Title")
	print(" - Track number")
	print(" - Artist")
	print(" - Album")
	print(" - Year")
	print(" - Genre")
	print("\nOn the TODO list is support for browsing songs on the command line, selecting specific songs to download, downloading entire artist discogs, downloading album art and maybe cleaning up existing untagged music files")
	print(f"{bcolors.FAIL}Piracy is illegal. Use this script at your own risk. I do not condone piracy in any way whatsoever.{bcolors.ENDC}")
	print()

	print("Enter full music directory or enter 'i' to setup dependencies")
	MUSIC_DIR = input(PROMPT)
	if MUSIC_DIR == "i":
		setup_dependencies()
	elif not MUSIC_DIR:
		MUSIC_DIR = "/home/jeff/Music"

	while True:
		print()
		print("What do you want to do?")
		print("q for quit")
		print("1. Download songs")
		print("2. Download albums")
		print("3. Download artist discography")

		ch = input(PROMPT)

		if ch == "1":
			download_songs()
		elif ch == "2":
			download_albums()
		elif ch == "3":
			download_discography()
		else:
			print("Unsupported option :( Please retry")


if __name__=="__main__":
	ytmusic = YTMusic()
	main()