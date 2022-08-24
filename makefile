THIS_FILE := $(lastword $(MAKEFILE_LIST))
.PHONY: help build up start down destroy stop restart logs ps db-shell
help:
	make -pRrq  -f $(THIS_FILE) \: 2>/dev/null | awk -v RS= -F\: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'
build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build $(c)
up-dev:
	docker-compose up $(c)
up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d  $(c)
start:
	docker-compose -f docker-compose.yml start $(c)
down-dev:
	docker-compose down $(c)
down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down $(c)
destroy:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v  $(c)
stop:
	docker-compose -f docker-compose.yml stop $(c)
restart:
	docker-compose -f docker-compose.yml stop $(c)
	docker-compose -f docker-compose.yml up -d $(c)
ps:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
logs:
	docker-compose -f docker-compose.yml logs --tail=1000 -f $(c)
flask-logs:
	docker-compose -f docker-compose.yml logs --tail=1000 -f flask
db-logs:
	docker-compose -f docker-compose.yml logs --tail=1000 -f mysqldb
nginx-logs:
	docker-compose -f docker-compose.yml logs --tail=1000 -f nginx
redis-logs:
	docker-compose -f docker-compose.yml logs --tail=1000 -f redis
rq-logs:
	docker-compose -f docker-compose.yml logs --tail=1000 -f rqworker
flask-shell:
	docker-compose -f docker-compose.yml exec flask /bin/bash
db-shell:
	docker-compose -f docker-compose.yml exec mysqldb mysql -u mcp_user -p master_control_program
nginx-shell:
	docker-compose -f docker-compose.yml exec nginx /bin/bash
redis-shell:
	docker-compose -f docker-compose.yml exec redis /bin/sh
rq-shell:
	docker-compose -f docker-compose.yml exec rqworker /bin/bash
