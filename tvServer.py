import sys
from subprocess import check_output, call
from random import shuffle
import socket
import json
import os
import threading
import time
import glob


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

 
def connection():
    TCP_IP = '192.168.0.102'
    TCP_PORT = 5005
    BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
    global run_event
   
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)
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
                conn.close()
        conn.close()

def ffmpeg(file):
    print file
    print "ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -acodec libfaac -vcodec libx264 -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4"
    fileType = file.split(".")
    fileType = fileType[len(fileType) - 1]
    if fileType == "mp4" or fileType == "m4v":
        call("ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -c copy -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4", shell=True)
    if fileType == "avi":
        call("ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -acodec libfaac -vcodec libx264 -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4", shell=True)



def player(path):
    global fileQueue
    global run_event
    try:
        print path
        f = open(fileQueue, "w")
        print "test"
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
        playlist = glob.glob(path[0])
        shuffle(playlist)
        del(path[0])
        f = open(fileQueue, "w+")
        output = ",".join(path)
        checksum = hash(output)
        f.write(output)
        f.close()
        for i in range(len(playlist) - 1):
            ffmpeg(playlist[i+1])
            path = getNextShows()
            newChecksum = hash(path) 
            if not run_event.is_set() or (newChecksum != checksum):
                break


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


global fileQueue = "/var/filequeue.csv"
main(sys.argv[1])
