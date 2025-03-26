help: echo help

rsa:
	python rsa.py

find_primes:
	gcc find_primes.c -o find_primes.exe
	find_primes.exe 99999 9999
