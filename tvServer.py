import sys
from subprocess import check_output, call
from random import shuffle
import socket
import json
import os
import threading
import time


def getPath(name):
    f = open('paths.json', 'r')
    key = json.loads(f.read())
    try:
        key[name]
    except NameError:
        return False
    else:
        return key[name]


def queueShow(path):
    fileQueue = "filequeue.csv"
    #open(fileQueue, "w+").close()
    try:
        f = open(fileQueue, "r")
    except:
        return False 
    if (len(f.read().split(",")) > 5):
        return False 
    f = open(fileQueue, "a")
    f.write(path + ",")
    return True 


def parseData(data):
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
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            print "received data:", data
            response = parseData(data)
            conn.send(str(response)) 

        conn.close()

def getArray(path, shuffled):
    path = path.replace('"', "")
    allFiles = filter(None, check_output("ls " + path.replace("'", "'\\''").replace(" ", "\ ") , shell=True, universal_newlines=True).split("\n"))
    if shuffled == True:
        for i in range(30):
            shuffle(allFiles)
    
    return allFiles;

def ffmpeg(file):
    print "ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -acodec libfaac -vcodec libx264 -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4"
    fileType = file.split(".")
    fileType = fileType[len(fileType) - 1]
    if fileType == "mp4" or fileType == "m4v":
        call("ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -c copy -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4", shell=True)
    if fileType == "avi":
        call("ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -acodec libfaac -vcodec libx264 -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4", shell=True)



def player(path):
    fileQueue = 'filequeue.csv'
    try:
        f = open(fileQueue, "w")
        f.write(path + ",")
        f.close()
    except:
        return False;
    global run_event
    while run_event.is_set():
        path = getNextShows()
        checksum = hash(path)
        path = path.split(",")
        print path
        playlist = getArray(path[0], True)
        del(path[0])
        f = open(fileQueue, "w")
        output = ",".join(path)
        checksum = hash(output)
        f.write(output)
        f.close()
        for i in range(len(playlist)):
            ffmpeg(playlist[i+1])
            path = getNextShows()
            newChecksum = hasih(path) 
            if not run_event.is_set() or (newChecksum != checksum):
                break


def getNextShows():
    fileQueue = "filequeue.csv"
    try:
        f = open(fileQueue, "r")
    except:
        "playlist ended"
        exit()
    path = f.read()
    f.close()
    return path    


def main():
    global run_event
    run_event = threading.Event()
    run_event.set()

    threads = []
    t1 = threading.Thread(target=player, args=("/home/david/Videos/The Simpsons/Playlist/*/*.avi",))
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

main()
