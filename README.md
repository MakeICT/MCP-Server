A re-write of the Master Control Program server at https://github.com/MakeICT/electronic-door

## Installation
1) Install Docker
2) Install Docker Compose
3) Clone repository
4) Build containers
   * `make build`

## Running
* Run the development environment
  * `make up-dev`
* Run the production environment
  * `make up`
* Stop the production environment
  * `make down`
* Destroy containers
  * `make destroy`
* Launch a terminal in a container
  * `docker exec -it <CONTAINER_NAME> /bin/bash`
* More make targets and their correseponding docker-compose commands can be found in the makefile

## Connecting
* The dev environment runs the server on port 5000
  * http://localhost:5000
* Default credentials are admin/admin