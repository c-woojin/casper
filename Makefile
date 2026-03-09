-include .env
export

run:
	./venv/bin/python scraper.py

loop:
	while true; do make run; sleep 300; done
