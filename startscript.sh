#!/bin/sh

LOGFILE=/home/pi/screen-master/startstopscript.log
RETAIN_NUM_LINES=20
for ((n=0;n<5;n++))
do
mapfile -n 20 < $LOGFILE
if ((${#MAPFILE[@]}>19)); then
    sed -i '1d' $LOGFILE
fi
done

function log {
    m_time=`date "+%F %T"`
    echo $m_time" "$1 >>$LOGFILE
}

#logsetup
log "Executed start screen command"
sleep 2
export DISPLAY=:0
python3 /home/pi/screen-master/screenApp.py