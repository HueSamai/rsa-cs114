help: echo help

rsa:
	python rsa.py

server_messenger:
	start_server.bat

client_messenger:
	start_client.bat

find_primes:
	gcc find_primes.c -o find_primes.exe
	find_primes.exe 99999 9999
