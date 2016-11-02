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
    json_data = json.loads(data)
    try:
        json_data['command']
    except NameError:
        return False
    else:
	if json_data['command'] == 'skip':
            print("skip!")
            print(call("killall ffmpeg", shell=True))
            return True

        if json_data['command'] == 'nextShow':
            path = getPath(json_data["tvShow"])
            if path != False:
                print str(path["name"]) + " has been queued."
            return str(queueShow(path["path"]))

        if json_data['command'] == 'idList':
            f = open('paths.json', 'r')
            key = json.loads(f.read())
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
    
    return "invalid command"


#Main connection thread. Calls the parseData function on success
 
def connection():
    TCP_PORT = 5005
    BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
    global run_event
    s = socket.socket()
    s.bind(("", TCP_PORT))
    s.listen(5)
    while run_event.is_set():
        conn, addr = s.accept()
        print 'Connection address:', addr
        while run_event.is_set():
            try:
                data = conn.recv(BUFFER_SIZE)
                if not data: break
                print "received data:", data
                response = parseData(data, conn)
                conn.send(str(response)) 
            except:
                break;
        conn.close()


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
        print path[0]
        playlist = glob.glob(path[0])
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


main(sys.argv[1])
