#!/bin/sh

game_name=justin_texas
game_script=main.py
log_dir=output/logs #日志目录
game_pid=output/game.pid

mkdir -p ${log_dir}

case $1 in
    start)
        python2.7 ${game_script} ${game_name}
        ;;
    stop)
        kill `cat ${game_pid}` && rm -f ${game_pid}
        ;;
    restart)
        source $0 stop
        sleep 1
        source $0 start
        ;;
    *)
        echo "Usage: ./start.sh start | stop | restart"
        ;;
esac
