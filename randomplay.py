import sys

from subprocess import check_output, call
from random import shuffle

allFiles = []

for path in sys.argv:
	path = path.replace('"', "")
	files = filter(None, check_output("ls " + "'" + path.replace("'", "'\\''") + "'" , shell=True, universal_newlines=True).split("\n"))
	allFiles = allFiles + files

for i in range(30):
	shuffle(allFiles)

for file in allFiles:
	print "ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -acodec libfaac -vcodec libx264 -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4"
	fileType = file.split(".")
	fileType = fileType[len(fileType) - 1]
	if fileType == "mp4" or fileType == "m4v":
		call("ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -c copy -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4", shell=True)
	if fileType == "avi":
		call("ffmpeg -re -i " + "'" + file.replace("'", "'\\''") + "'" + " -acodec libfaac -vcodec libx264 -f flv rtmp://djwt.xyz:420/live/mp4:test.mp4", shell=True)
exit()

