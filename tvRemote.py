import socket
import sys
import json

TCP_IP = '192.168.0.102'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "test data"

if sys.argv[1] == "help":
    print("skip: skips the current episode")
    print("nextShow <id>: queues the next show")
    print("idList: returns a list of program IDs")
    print("currentEpisode: returns the current episode")
    exit()

try:
    path = sys.argv[2]
except:
    path = ""
data = {'command' : sys.argv[1], 'tvShow': path} 


MESSAGE = json.dumps(data, ensure_ascii=False)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode())
data = s.recv(BUFFER_SIZE)

print(str(data))

s.close()
