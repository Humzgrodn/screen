#!/bin/sh

LOGFILE=/home/pi/screen-master/startstopscript.log


function log {
    m_time=`date "+%F %T"`
    echo $m_time" "$1 >>$LOGFILE
}

#logsetup
log "Executed stop screen command"
export DISPLAY=:0
pkill -2 python3