import sys
from subprocess import check_output, call
from random import shuffle
import socket
import json
import os
import threading
import time
import glob
import hashlib
from natsort import natsorted, ns

#Retrieves a show path from a keyword

def getPath(name):
    f = open('/home/david/Documents/tvSocket/paths.json', 'r')
    key = json.loads(f.read())
    try:
        key[name]
    except NameError:
        return False
    else:
        return key[name]

#Recieves a path, and adds it to the show queue

def queueShow(path):
    global fileQueue
    #open(fileQueue, "w+").close()
    try:
        f = open(fileQueue, "r")
    except:
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

#Invokes the approriate function upon recieving a valid json

def parseData(data, conn):
    global shuffleToggle
    global skipLock
    json_data = json.loads(data)
    try:
        json_data['command']
    except NameError:
        return False
    else:
	if json_data['command'] == 'skip':
            print skipLock
            if skipLock == False:
                print("skip!")
                print(call("killall ffmpeg", shell=True))
                return True
            else:
                return "Skiplock enabled. Contact your administrator to release it."

        if json_data['command'] == 'nextShow':
            path = getPath(json_data["tvShow"])
            if path != False:
                print str(path["name"]) + " has been queued."
            return str(queueShow(path["path"]))

        if json_data['command'] == 'idList':
            f = open('/home/david/Documents/tvSocket/paths.json', 'r')
            ##key = json.loads(f.read())
            key = f.read().strip()
            return key

        if json_data['command'] == 'currentEpisode':
            global currentEpisode
            return currentEpisode

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
        if json_data['command'] == 'pickEpisode':
            try:
                json_data['tvShow']
            except:
                return False
            else:
                return queueEpisode(json_data['tvShow'])
 

    return "invalid command"

def queueEpisode(episodeKey):
    global run_event
    global currentShow
    episodeKey = episodeKey.split(":")
    if len(episodeKey) != 2:
        return "invalid syntax"
    for i in range(2):
    	try:
            int(episodeKey[i])
        except:
            return "not numbers"
        episodeKey[i] = int(episodeKey[i]) - 1
    currentShowSplit = currentShow.split("/")
    episodePath = ""
    for i in range((len(currentShowSplit) - 2)):
        if currentShowSplit[i] != "":
            episodePath = episodePath + "/" + currentShowSplit[i]
    episodePath = nthFile(episodePath, "dir", episodeKey[0])
    episodePath = nthFile(episodePath, currentShow.split(".")[len(currentShow.split(".")) - 1], episodeKey[1])
    print episodePath
    try:
        queueShow(episodePath)
        #queueShow(currentShow)
    except:
        return False
    else:
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
        print subject
        print natsorted(subject, alg=ns.IGNORECASE)
        for f in natsorted(subject, key=lambda y: y.lower()):
            print "test"
            filePath = os.path.join(subdir, f)
            if fileType == "dir":
                if counter == n:
                    return filePath
            else:
                if filePath.split(".")[len(filePath.split(".")) - 1] == fileType:
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
            print "received data:", data
            response = parseData(data, conn)
            print data
            conn.send(str(response).encode())
        except:
            break;
    conn.close()

#Main connection thread. Calls the parseData function on success

def connection():
    TCP_PORT = 5005
    BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
    global run_event
    global skipLock
    skipLock = False
    s = socket.socket()
    s.bind(("", TCP_PORT))
    s.listen(5)
    threads = []
    while run_event.is_set():
        conn, addr = s.accept()
        print 'Connection address:', addr
        #connected(conn, BUFFER_SIZE)
        newthread = threading.Thread(target=connected, args=(conn, BUFFER_SIZE, ))
        newthread.start()
        threads.append(newthread)


#Calls the approriate ffmpeg command for a given file

def ffmpeg(file):
    fileType = file.split(".")
    fileType = fileType[len(fileType) - 1]
    f = open('/home/david/Documents/tvSocket/filetypes.json', 'r')
    key = json.loads(f.read())
    try:
        print key
        print fileType
        key[fileType]
    except:
        print "Invalid file type"
        return False
    else:
        command = key[fileType] % ("'" + file.replace("'", "'\\''") + "'")
        print command
        call(command, shell=True)


#Intitiate the stream, and check for queued show changes

def player(path):
    global fileQueue
    global run_event
    global currentEpisode
    global shuffleToggle
    global currentShow

    try:
        f = open(fileQueue, "w")
        f.write(path + ",")
        f.close()
    except:
        print "could not open file"
        run_event.clear()
        return False;
    while run_event.is_set():
        path = getNextShows()
        checksum = hash(path)
        path = path.rstrip(',').split(",")
        print path
        if path[0] == "":
            print "test"
            path[0] = currentShow
        currentShow = path[0]
        playlist = glob.glob(path[0])
        if shuffleToggle == True:
            shuffle(playlist)
        del(path[0])
        enqueued = False
        if len(path) > 0:
            enqueued = True
        f = open(fileQueue, "w+")
        output = ",".join(path)
        checksum = hash(output)
        f.write(output)
        f.close()
        for i in range(0, len(playlist)):
            currentEpisode = os.path.dirname(playlist[i]).split("/")
            currentEpisode = currentEpisode[len(currentEpisode) - 1] + " - " + os.path.splitext(os.path.basename(playlist[i]))[0]
            ffmpeg(playlist[i])
            path = getNextShows()
            newChecksum = hash(path)
            if not run_event.is_set() or (newChecksum != checksum) or (enqueued == True):
                break


#Returns an array of containing the queued shows

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


#Initiate threads, then wait for program termination.

def main(path):
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
        print "attempting to close threads."
        run_event.clear()
        t1.join()
        t2.join()
        print "threads successfully closed"

#global currentShow
#currentShow = "/home/david/Videos/The Simpsons/Playlist/*/*.avi"
#global run_event
#run_event = threading.Event()
#run_event.set()
#connection()
try:
    sys.argv[1]
except:
    path = "/home/david/Videos/The Simpsons/Playlist/*/*.avi"
else:
    path = sys.argv[1]
main(path)
