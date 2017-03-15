import sys
import time
import subprocess
from random import shuffle
import socket
import json
import os
import threading
import time
import glob
import hashlib
from natsort import natsorted, ns


def togglePause():
    print("test")
    pid = subprocess.Popen("ps -A -o pid,cmd|grep ffmpeg | grep -v grep |head -n 1 | awk '{print $1}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    cmd = "ps " + pid + " | grep " + pid + " | awk '{print $3}'"
    status = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    print(status)
    if status[0] == 'S':
        cmd = "kill -TSTP " + pid
    elif status[0] == 'T':
        cmd = "kill -CONT " + pid
    else:
        return "Unknown Status"
    try:
        print(cmd)
        subprocess.Popen(cmd, shell=True)
    except:
        return False
    else:
        return True


def createPlaylist(name):
    f = open('/home/david/Documents/tvSocket/playlists.json', 'r')
    key = json.loads(f.read())
    try:
        key[name]
    except NameError:
        key[name] = {}
        f.close()
        f = open('/home/david/Documents/tvSocket/playlists.json', 'w+')
        f.write(json.dumps(key))
        f.close()
        return True
    else:
        return "That Playlist Already Exists"


def getPlaylistStringFromId(item):
    playlistContent = getPlaylistData(item[1:])
    playlistString = ""
    for i in range(len(playlistContent)):
        playlistString = playlistString + "|" + playlistContent[str(i)]
    return playlistString[1:]


def getPathCollection(id, field=False):    
    splitIds = id.split('|')
    if field != False:
        returnString = ""
        for i in splitIds:
            if i[0] == '^':
                returnString = returnString + getPathCollection(getPlaylistStringFromId(i), field)
            else:
                showData = getShowData(i.split(':')[0])
                try:
                    showData[field]
                except:
                    continue
                else:
                    returnString = returnString + showData[field] + ", "
        return returnString.rstrip(', ')
    paths = []
    for item in splitIds:
        if item[0] == '^':
            playlistString = getPlaylistStringFromId(item)
            paths.extend(getPathCollection(playlistString))
        else:
            path = queueEpisode(item)
            paths.extend(glob.glob(path))
    return paths


# Retrieves a show path from a keyword

def getShowData(name):
    f = open('/home/david/Documents/tvSocket/paths.json', 'r')
    key = json.loads(f.read())
    try:
        key[name]
    except NameError:
        return False
    else:
        return key[name]


def getPlaylistData(name):
    f = open('/home/david/Documents/tvSocket/playlists.json', 'r')
    key = json.loads(f.read())
    try:
        key[name]
    except NameError:
        return False
    else:
        return key[name]


def getNameFromValue(path, searchType):
    f = open('/home/david/Documents/tvSocket/paths.json', 'r')
    showArray = json.loads(f.read())
    for key, value in showArray.items():
        try:
            value[searchType]
        except NameError:
            continue
        else:
            if value[searchType] == path:
                return value['name']
    return "Unknown Show"


# Receives a path, and adds it to the show queue

def queueShow(path):
    global fileQueue
    try:
        f = open(fileQueue, "r")
    except:
        print("could not read")
        return False
    if (len(f.read().rstrip(',').split(",")) > 5):
        return False
    f = open(fileQueue, "a")
    f.write(path + ",")
    return True


def requestVideo(name):
    try:
        requestsFile = "/home/david/Documents/tvSocket/requests.json"
        f = open(requestsFile, 'a+')
        contents = f.read()
        if contents != "":
            requests = json.loads(contents)
        else:
            requests = []
        f.close()
        requests.append(name)
        f = open(requestsFile, "w+")
        f.write(json.dumps(requests))
        f.close()
    except:
        return False
    else:
        return True


def hashPass(password, salt):
    return hashlib.sha224(password + salt).hexdigest()


def authenticate(conn):
    BUFFER_SIZE = 1024
    conn.send("%auth")
    data = conn.recv(BUFFER_SIZE)
    try:
        f = open("/home/david/Documents/tvSocket/.users.json")
        users = json.loads(f.read())
        for i in range(len(users)):
            if hashPass(users[i]['hash'], users[i]['salt']) == hashPass(hashPass(data, users[i]['salt']), users[i]['salt']):
                return True
        return False
    except:
        return False


def formattedList():
    f = open('/home/david/Documents/tvSocket/paths.json', 'r')
    key = json.loads(f.read())
    outputString = ""
    for i, value in key.items():
        # outputString = outputString + value['name'] + " - " + i + "\n"
        outputString = outputString + i + ", "
    ##key = f.read().strip()
    return outputString.rstrip(", ")


# Invokes the approriate function upon recieving a valid json

def parseData(data, conn):
    global shuffleToggle
    global skipLock
    global episodeChangeEvent
    json_data = json.loads(data)
    try:
        json_data['command']
    except NameError:
        return False
    else:
        if json_data['command'] == 'skip':
            print(skipLock)
            if skipLock == False:
                print("skip!")
                print(subprocess.call("killall ffmpeg", shell=True))
                episodeChangeEvent.wait()
                return currentEpisode
            else:
                return "Skiplock enabled. Contact your administrator to release it."

        if json_data['command'] == 'nextShow':
            path = getPathCollection(json_data["tvShow"])
            if path != False:
                print(str(getPathCollection(json_data["tvShow"], "name")) + " has been queued.")
                return str(queueShow(json_data["tvShow"]))
            else:
                print("something went wrong")  # tfw windows 10
                return "No such show"

        if json_data['command'] == 'idList':
            return formattedList()
        
        if json_data['command'] == 'currentShow':
            global currentShowName
            return currentShowName
        
        if json_data['command'] == 'currentEpisode':
            global currentEpisode
            return currentEpisode

        if json_data['command'] == 'pause':
            return togglePause()

        if json_data['command'] == 'request':
            return requestVideo(json_data['tvShow'])

        if json_data['command'] == 'approve':
            if authenticate(conn) == True:
                f = open("/home/david/Documents/tvSocket/requests.json", "r")
                return json.loads(f.read())
            else:
                return "Invalid password"
        if json_data['command'] == 'skipLock':
            if authenticate(conn) == False:
                return False
            try:
                json_data['tvShow']
            except:
                return False
            else:
                if json_data['tvShow'] == "True":
                    skipLock = True
                    return True
                elif json_data['tvShow'] == "False":
                    skipLock = False
                    return True
                else:
                    return False
        if json_data['command'] == 'toggleShuffle':
            try:
                json_data['tvShow']
            except:
                return False
            else:
                if json_data['tvShow'] == "True": 
                    shuffleToggle = True
                    return True
                if json_data['tvShow'] == "False":
                    shuffleToggle = False
                    return True
                else:
                    return False
        if json_data['command'] == 'createPlaylist':
            return createPlaylist(json_data['tvShow'])

    return "Invalid command"


def queueEpisode(episodeKey):
    global run_event
    global currentShow
    episodeKey = episodeKey.split(":")
    if (len(episodeKey) > 3) or (len(episodeKey) < 1):
        return "invalid syntax"
    elif len(episodeKey) == 1:
        return getShowData(episodeKey[0])['path']
    for i in range(2):
    	try:
            int(episodeKey[i+1])
        except:
            return "not numbers"
        episodeKey[i+1] = int(episodeKey[i+1]) - 1
    try:
        episodeKey[0]
    except:
        show = currentShow
    else:
        show = getShowData(episodeKey[0])['path']
        if show == False:
            return show
    showSplit = show.split("/")
    episodePath = ""
    for i in range((len(showSplit) - 2)):
        if showSplit[i] != "":
            episodePath = episodePath + "/" + showSplit[i]
    episodePath = nthFile(episodePath, "dir", episodeKey[1])
    if len(show.split(".")) > 1:
        showExtension = show.split(".")[len(show.split(".")) - 1]
    else:
        showExtension = False
    episodePath = nthFile(episodePath, showExtension, episodeKey[2])
    print(episodePath)
    #try:
    #    queueShow(episodePath)
    #except:
    #    return False
    #else:
    return episodePath


def nthFile(path, fileType, n):
    counter = 0
    try:
        int(n)
    except:
        return False
    else:
        n = int(n)
    for subdir, dirs, files in os.walk(path):
        if fileType == "dir":
            subject = dirs
        else:
            subject = files
        print(subject)
        print(natsorted(subject, alg=ns.IGNORECASE))
        for f in natsorted(subject, key=lambda y: y.lower()):
            filePath = os.path.join(subdir, f)
            if fileType == "dir":
                if counter == n:
                    return filePath
            else:
                if (filePath.split(".")[len(filePath.split(".")) - 1] == fileType) or (fileType == False):
                    if counter == n:
                       return filePath
            counter += 1
    return False
    

def connected(conn, BUFFER_SIZE):
    global run_event
    while run_event.is_set():
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            print("received data:", data)
            response = parseData(data, conn)
            print(data)
            conn.send(str(response).encode())
        except:
            break;
    conn.close()


# Main connection thread. Calls the parseData function on success

def connection():
    TCP_PORT = 5005
    BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
    global run_event
    global skipLock
    skipLock = False
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", TCP_PORT))
    s.listen(5)
    threads = []
    while run_event.is_set():
        conn, addr = s.accept()
        print('Connection address:', addr)
        #connected(conn, BUFFER_SIZE)
        newthread = threading.Thread(target=connected, args=(conn, BUFFER_SIZE, ))
        newthread.start()
        threads.append(newthread)


# Calls the approriate ffmpeg command for a given file

def ffmpeg(file, fileKey):
    fileType = file.split(".")
    fileType = fileType[len(fileType) - 1]
    f = open('/home/david/Documents/tvSocket/filetypes.json', 'r')
    key = json.loads(f.read())
    try:
        params = getShowData(fileKey)['params']
    except:
        params = ""
    try:
        key[fileType]
    except:
        print("Invalid file type")
        return False
    else:
        command = key[fileType] % ("'" + file.replace("'", "'\\''") + "'", params)
        print(command)
        subprocess.call(command, shell=True)


# Intitiate the stream, and check for queued show changes

def player(path):
    global fileQueue
    global run_event
    global currentEpisode
    global shuffleToggle
    global currentShow
    global currentShowName
    global episodeChangeEvent
    
    try:
        f = open(fileQueue, "w")
        f.write(path + ",")
        f.close()
    except:
        print("could not open file")
        run_event.clear()
        return False;
    while run_event.is_set():
        showqueue = getNextShows()
        showqueue = showqueue.rstrip(',').split(",")
        if showqueue[0] == "":
            showqueue[0] = currentShow
        currentShow = showqueue[0]
        currentShowName = getPathCollection(currentShow, 'name')
        currentShowPath = getPathCollection(currentShow)
        try:
            f = open('/var/www/html/currentShow.txt', 'w')
        except:
            print("Website episode name not set")
        else:
            f.write(currentShowName)
            f.close()
        
        playlist = currentShowPath
        print(playlist)
        if shuffleToggle == True:
            shuffle(playlist)
        del(showqueue[0])
        enqueued = False
        if len(showqueue) > 0:
            enqueued = True
        f = open(fileQueue, "w+")
        output = ",".join(showqueue)
        checksum = hash(output)
        f.write(output)
        f.close()
        for i in range(0, len(playlist)):
            currentEpisode = os.path.dirname(playlist[i]).split("/")
            currentEpisode = currentEpisode[len(currentEpisode) - 1] + " - " + os.path.splitext(os.path.basename(playlist[i]))[0]
            episodeChangeEvent.set()
            episodeChangeEvent.clear()
            ffmpeg(playlist[i], currentShow)
            path = getNextShows()
            newChecksum = hash(path)
            if not run_event.is_set() or (newChecksum != checksum) or (enqueued == True):
                break


# Returns an array of containing the queued shows

def getNextShows():
    global fileQueue
    try:
        f = open(fileQueue, "r")
    except:
        "playlist ended"
        exit()
    path = f.read()
    f.close()
    return path


# Initiate threads, then wait for program termination.

def main(path):
    global currentShowName
    currentShowName = "The Simpsons"
    global currentShow
    currentShow = path
    global shuffleToggle
    shuffleToggle = True
    global run_event
    run_event = threading.Event()
    run_event.set()
    global fileQueue
    fileQueue = "/var/filequeue.csv"
    global currentEpisode
    currentEpisode = "UNSET"
    global episodeChangeEvent
    episodeChangeEvent = threading.Event()
    
    threads = []
    t1 = threading.Thread(target=player, args=(path,))
    threads.append(t1)
    t1.start()
    t2 = threading.Thread(target=connection)
    threads.append(t2)
    t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("attempting to close threads.")
        run_event.clear()
        t1.join()
        t2.join()
        print("threads successfully closed")

#global currentShow
#currentShow = "/home/david/Videos/The Simpsons/Playlist/*/*.avi"
#global fileQueue
#fileQueue = "/var/filequeue.csv"
#global run_event
#run_event = threading.Event()
#run_event.set()
#connection()
try:
    sys.argv[1]
except:
    path = 'simpsons'
else:
    path = sys.argv[1]
main(path)
