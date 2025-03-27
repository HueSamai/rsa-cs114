import rsa
import time
import stdio

def main():
    N = 300_000
    b = 98765
    p = 1234567
    n = 1234567890

    start = time.time_ns()
    for _ in range(N):
        rsa.powmod(b, p, n)
    end = time.time_ns()
    stdio.writeln(f"BITWISE POWMOD:\t\t {(end - start) / N}ns")

    start = time.time_ns()
    for _ in range(N):
        rsa.powmod2(b, p, n)
    end = time.time_ns()
    stdio.writeln(f"\"REGULAR\" POWMOD:\t {(end - start) / N}ns")

    start = time.time_ns()
    rsa.powmod3(b, p, n)
    end = time.time_ns()
    stdio.writeln(f"NAIVE POWMOD:\t\t {(end - start)}ns")

if __name__ == "__main__":
    main()
