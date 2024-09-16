all: build

build:
	docker-compose build --no-cache

clean:
	docker-compose down --volumes --remove-orphans
	docker system prune -af

run:
	docker-compose up
	
stop:
	docker-compose down

rebuild: clean build run

rerun:
	docker-compose down --volumes --remove-orphans
	docker-compose up 
