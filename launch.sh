#!/bin/bash
/usr/local/nginx/sbin/nginx
nohup python /home/david/Documents/tvSocket/tvServer.py > /var/log/tvserver.log &
iptables -F
