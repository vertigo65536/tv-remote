import sys
from subprocess import check_output, call
from random import shuffle
import socket
import json
import os
import threading
import time
import glob


#Retrieves a show path from a keyword

def getPath(name):
    print "getPath"
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
    print "queueShow"
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


#Invokes the approriate function upon recieving a valid json

def parseData(data):
    json_data = json.loads(data)
    print "parseData"
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
                response = parseData(data)
                conn.send(str(response)) 
            except:
                break;
        conn.close()


#Calls the approriate ffmpeg command for a given file

def ffmpeg(file):
    fileType = file.split(".")
    fileType = fileType[len(fileType) - 1]
    f = open('/home/david/Documents/tvSocket/filetypes.json', 'r')
#    print f.read()
    key = json.loads(f.read())
    try:
        print key
        key[fileType]
    except:
        print "Invalid file type"
    else:
        command = key[fileType] % ("'" + file.replace("'", "'\\''") + "'")
        call(command, shell=True)


#Intitiate the stream, and check for queued show changes

def player(path):
    global fileQueue
    global run_event

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
        for i in range(len(playlist) - 1):
            ffmpeg(playlist[i+1])
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
        print "attempting to close threads. Max wait =",max(1,2)
        run_event.clear()
        t1.join()
        t2.join()
        print "threads successfully closed"


global fileQueue
fileQueue = "/var/filequeue.csv"
main(sys.argv[1])
