#!/bin/bash

SCR_IP=${1}
DST_IP=${2}
SIZE=${3}

COUNTER=1
echo $COUNTER
while true
do
    for ((i = 0; i < 100; i++))
    do
        sudo sendip -p ipv4 -p udp -is ${SCR_IP} -us $((5000 + ${i})) -ud 5000 -d r${SIZE} ${DST_IP}
        ((COUNTER++))
    done
done