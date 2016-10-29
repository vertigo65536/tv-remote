import socket
import json

TCP_IP = '192.168.0.102'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "test data"

#data = {'command' : 'idList'}  #idList will return a json matching the key to the show name
#data = {'command' : 'nextShow', 'tvShow' : 'simpsons'} #Sets the next show to watch
data = {'command' : 'skip'} #Skips the current episode, and initiates next show if set


MESSAGE = json.dumps(data, ensure_ascii=False)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode())
data = s.recv(BUFFER_SIZE)

print(str(data))

s.close()
