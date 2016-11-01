import hashlib
import random
import sys
import json
import getpass

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
chars = []
for i in range(24):
    chars.append(random.choice(ALPHABET))

salt = ''.join(chars)

password = getpass.getpass("enter password: ")
hashPass = hashlib.sha224(password + salt).hexdigest()

userFile = "/home/david/Documents/tvSocket/.users.json"
try:
    f = open(userFile, "a+")
    contents = f.read()
    if contents != "":
        users = json.loads(contents)
    else:
        users = []
    f.close()
    users.append({'hash': hashPass, 'salt': salt})
    f = open(userFile, "w+")
    f.write(json.dumps(users))
    f.close()
except:
    print "failed"
else:
    print "success"
