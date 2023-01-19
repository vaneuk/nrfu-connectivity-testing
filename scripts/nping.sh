#!/bin/bash

DST_IP=${1}
SIZE=${2}
FLOWS=${3}
DELAY=${4}

echo STARTING WITH PACKET SIZE "$SIZE", FLOWS: "$FLOWS"

for ((i = 0; i <= FLOWS; i++))
do
  echo START "$i"/"$FLOWS", IP: "$IP"
  nping --udp -g $((5000 + ${i})) -p 5000 --data-length ${SIZE} -c 0 ${DST_IP} --delay ${DELAY}ms >/dev/null 2>&1 &
done

echo FINISHED
