if [ $EUID != 0 ]; then
    sudo "$0" "$@"
    exit $?
fi
bash start_webserver.sh
bash start_publiclog.sh
while [ ! -f nohup.out ]
do
  sleep 2
done
tail -f nohup.out
