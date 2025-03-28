import random
from typing import Tuple, Union
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
    result = 1

    while p > 0:
        # if the last bit of p is 1, mutliply the result by b
        if p & 1:
            result = (result * b) % n

        # shift p to the right
        p >>= 1

        # b iterates through the original b to the power of all powers of 2
        b = (b*b) % n

    return result

"""
powmod2: power modulus, without bitwise operations
b: base
p: power
n: modulus

returns: (b**p) % n
"""
def powmod2(b: int, p: int, n: int):
    result = 1

    while p > 0:
        # if the last bit of p is 1, mutliply the result by b
        if p & 1:
            result = (result * b) % n

        # shift p to the right
        p >>= 1

        # b iterates through the original b to the power of all powers of 2
        b = (b*b) % n

    return result

"""
powmod3: power modulus, naive approach, no optimisations
b: base
p: power
n: modulus

returns: (b**p) % n
"""
def powmod3(b: int, p: int, n: int):
    return ((b % n) ** p) % n

"""
extended_euclidean: calculates the t value in bezout's identity for a and b

a,b: (int) values to use in bezout's identity

returns: (int) t
"""
def extended_euclidean(a: int, b: int):
    r0 = a
    r1 = b

    t0 = 0
    t1 = 1

    while r1 != 0:
        # temporary variables, used to swap r0 and r1, and t0 and t1
        tmp_r1 = r1
        tmp_t1 = t1

        # find the quotient
        q = r0 // r1
        
        # calculate new r1 and set r0 to old r1
        r1 = r0 - q * r1
        r0 = tmp_r1
        
        # calculate new t1 and set t0 to old t1
        t1 = t0 - q * t1
        t0 = tmp_t1

    return t0

"""
encrypt: encrypt plaintext message 'M', with public key 'e' and 'n'

M: (int) plaintext message
e: (int) public key exponent
n: (int) modulus

returns: (int) encrypted message
""" 
def encrypt(M: int, e: int, n: int):
    return powmod(M,e,n)

"""
decrypt: decrypt encrypted message 'C', with private key 'd' and modulus 'n'

C: (int) encrypted message
d: (int) private key
n: (int) modulus

returns: (int) decrypted message
"""
def decrypt(C: int, d: int, n: int):
    return powmod(C,d,n)


CHARS_PER_ENCRYPTED_NUM = 8 
CHARS_PER_DECRYPTED_NUM = 4

"""
encrypt_string: encrypts a string

string: (str) string to encrypt
e: (int) public key
n: (int) modulus

returns: (bytes) the bytes of the encrypted string
"""
def encrypt_string(string: str, e: int, n: int) -> bytes:
    # get ASCII value for each character
    char_values = []
    for char in string:
        char_values += [ord(char)]
    
    # pad the character values with zeroes
    padding_amt = CHARS_PER_DECRYPTED_NUM - len(char_values) % CHARS_PER_DECRYPTED_NUM
    char_values += [0]*padding_amt
    
    # convert to byte list
    char_values = bytes(char_values)

    nums = bytes(0) 
    for i in range(0,len(char_values),CHARS_PER_DECRYPTED_NUM):
        num_bytes = char_values[i:i + CHARS_PER_DECRYPTED_NUM]
        
        # treat the character bytes as the bytes of a big endian number.
        # it's important for it to be big endian, because values that are too small 
        # are susceptible to attacks to figure out the private key, because the encrypted
        # number values are too small.
        num = int.from_bytes(num_bytes, "big")
        nums += encrypt(num, e, n).to_bytes(CHARS_PER_ENCRYPTED_NUM, "big")   

    return nums


"""
decrypt_string: decrypts an encrypted bytes object into a string

encrypted_msg: (bytes) the encrypted bytes which will be decrypted
d: (int) private key
n: (int) modulus

returns: (str) the decrypted string 
"""
def decrypt_string(encrypted_msg: bytes, d: int, n: int):
    string = ""
    
    # for every number in our encrypted message
    for i in range(0,len(encrypted_msg),CHARS_PER_ENCRYPTED_NUM):
        # get the number's bytes
        num_bytes = encrypted_msg[i:i+CHARS_PER_ENCRYPTED_NUM]
        num = int.from_bytes(num_bytes, "big")
        
        # decrypt it and convert it to bytes
        decrypted_num = decrypt(num, d, n)
        decrypted_num_bytes = decrypted_num.to_bytes(CHARS_PER_DECRYPTED_NUM, "big") 
        
        # treat each byte of the decrypted number as a character and add it to the string
        for byte in decrypted_num_bytes:
            if byte == 0: continue 
            string += chr(byte)

    return string

"""
generate_keys: generates a random private and public key

returns: (int,int,int) private key, public key, modulus n

if failed to generate keys will return None,None,None
"""
def generate_keys() -> Union[Tuple[int,int,int], Tuple[None,None,None]]:
    global primes
    if len(primes) == 0:
        load_primes()

    p = rand_prime()
    q = rand_prime()
    while q == p:
        q = rand_prime()

    n = p * q

    l = (p - 1) * (q - 1)
    
    i = 0
    e = rand_prime()
    while e >= l and i < 100:
        e = rand_prime()
        i += 1

    if e >= l:
        return None,None,None

    d = extended_euclidean(l, e) % l

    return d,e,n
        

def main():
    d,e,n = generate_keys() 

    if d is None or e is None or n is None:
        stdio.writeln("ERROR: failed to generate keys")
        exit(1)

    M = 121 
    stdio.writeln(f"M: {M}")

    C = encrypt(M, e, n)
    stdio.writeln(f"C: {C}")

    m = decrypt(C, d, n)
    stdio.writeln(f"m: {m}")

    msg = "this is a new message :)"
    stdio.writeln(msg)

    encrypted_msg = encrypt_string(msg, e, n)
    stdio.writeln(str(encrypted_msg))

    decrypted_msg = decrypt_string(encrypted_msg, d, n)
    stdio.writeln(decrypted_msg)

if __name__ == "__main__":
    main()
