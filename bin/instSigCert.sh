#!/bin/bash

for i in `ls /mnt/stend/certs`
do
  
  if [ "$i" != "`hostname`.cer" ]
  then
    fn="/mnt/stend/certs/"$i
    echo "o" | /opt/cprocsp/bin/amd64/certmgr -inst -f $fn
  fi
done
