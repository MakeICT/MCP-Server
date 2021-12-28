#!/bin/bash
# source venv/bin/activate
while true; do
    # flask db upgrade
    if [ $FLASK_ENV == "development" ]
    then
    #     flask db upgrade
        flask setup default
    else
        flask setup default
    fi
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done    
# rq worker --url redis://redis:6379 mcp-tasks
# flask translate compile
# exec gunicorn -b :5000 --access-logfile - --error-logfile - microblog:app
# exec flask run --host=0.0.0.0
cd src/
# exec gunicorn -k flask_sockets.worker -b localhost:5000 -w 4 run:app
echo $FLASK_ENV
echo $DATABASE_URL
if [ $FLASK_ENV == "development" ]
then
    exec gunicorn -k flask_sockets.worker -b 0.0.0.0:5000 -w 1 --reload --max-requests 1 --graceful-timeout 0 run:app 
else
    exec gunicorn -k flask_sockets.worker -b 0.0.0.0:8000 -w 4 run:app
fi