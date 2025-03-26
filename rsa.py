import random
import stdio

primes = []
"""
load_primes: loads primes from prime.txt into global list 'primes', with each prime being on a separate line
"""
def load_primes():
    global primes
    with open("primes.txt", "r") as file:
        for line in file:
            primes += [int(line.strip())]

"""
rand_prime: get a random prime

returns: (int) a random prime
"""
def rand_prime():
    global primes
    return random.choice(primes)

"""
powmod: power modulus
b: base
p: power
n: modulus

returns: (b**p) % n
"""
def powmod(b: int, p: int, n: int):
    # result stores the result of the modular exponentiation
    result = 1

    # stores which power of 2 we are busy checking
    mask = 1
    
    # once our mask reaches values greater than p we know there are no more powers of 2 left
    while mask <= p:
        # if the current masked bit of p is 1, it means we should multiply by b
        if mask & p:
            result = (result * b) % n

        # b iterates through the original b to the power of all powers of 2
        b = (b*b) % n

        # bit shift the mask to the left (same as multiplying by 2)
        mask <<= 1

    return result

"""
extended_euclidean: calculates the t value in bezout's identity for a and b

a,b: (int) values to use in bezout's identity

returns: (int) t
"""
def extended_euclidean(a, b):
    r0 = a
    r1 = b

    t0 = 0
    t1 = 1

    while r1 != 0:
        tmp_r1 = r1
        tmp_t1 = t1

        q = r0 // r1
        r1 = r0 - q * r1
        r0 = tmp_r1

        t1 = t0 - q * t1
        t0 = tmp_t1

    return t0 % a

"""
encrypt: encrypt plaintext message 'M', with public key 'e' and 'n'

M: (int) plaintext message
e: (int) public key exponent
n: (int) modulus

returns: (int) encrypted message
""" 
def encrypt(M, e, n):
    return powmod(M,e,n)

"""
decrypt: decrypt encrypted message 'C', with private key 'd' and modulus 'n'

C: (int) encrypted message
d: (int) private key exponent
n: (int) modulus

returns: (int) decrypted message
"""
def decrypt(C, d, n):
    return powmod(C,d,n)

def encrypt_string(string, e, n):
    C = []
    for char in string:
        C += [encrypt(ord(char), e, n)]

    return C

def decrypt_string(C, d, n):
    M = ""
    for c in C:
        M += chr(decrypt(c, d, n))
    return M

def main():
    load_primes()

    p = rand_prime()
    q = rand_prime()
    while q == p:
        q = rand_prime()
    n = p * q

    l = (p - 1) * (q - 1)
    stdio.writeln(f"p: {p}, q: {q}, n: {n}, l: {l}")
    
    i = 0
    e = rand_prime()
    while e >= l and i < 100:
        e = rand_prime()
        i += 1

    if e >= l:
        stdio.writeln("ERROR: couldn't find value for e")
        exit(1)

    d = extended_euclidean(l, e)
    stdio.writeln(f"e: {e}, d: {d}, ed (mod n): {(e * d) % l}")

    M = 50
    stdio.writeln(f"M: {M}")

    C = encrypt(M, e, n)
    stdio.writeln(f"C: {C}")

    m = decrypt(C, d, n)
    stdio.writeln(f"m: {m}")

    msg = "Hello, World!"
    stdio.writeln(msg)

    encrypted_msg = encrypt_string(msg, e, n)
    stdio.writeln(str(encrypted_msg))

    decrypted_msg = decrypt_string(encrypted_msg, d, n)
    stdio.writeln(decrypted_msg)

if __name__ == "__main__":
    main()
