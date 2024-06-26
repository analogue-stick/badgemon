When designing the prototype there are some considerations to be made to ease porting to micropython.

## Libraries
MicroPython does not have every available library imaginable. Try to avoid using libraries not in this list:
- [`array` – arrays of numeric data](https://docs.micropython.org/en/latest/library/array.html)
- [`asyncio` — asynchronous I/O scheduler](https://docs.micropython.org/en/latest/library/asyncio.html)
- [`binascii` – binary/ASCII conversions](https://docs.micropython.org/en/latest/library/binascii.html)
- [`builtins` – builtin functions and exceptions](https://docs.micropython.org/en/latest/library/builtins.html)
- [`cmath` – mathematical functions for complex numbers](https://docs.micropython.org/en/latest/library/cmath.html)
- [`collections` – collection and container types](https://docs.micropython.org/en/latest/library/collections.html)
- [`errno` – system error codes](https://docs.micropython.org/en/latest/library/errno.html)
- [`gc` – control the garbage collector](https://docs.micropython.org/en/latest/library/gc.html)
- [`gzip` – gzip compression & decompression](https://docs.micropython.org/en/latest/library/gzip.html)
- [`hashlib` – hashing algorithms](https://docs.micropython.org/en/latest/library/hashlib.html)
- [`heapq` – heap queue algorithm](https://docs.micropython.org/en/latest/library/heapq.html)
- [`io` – input/output streams](https://docs.micropython.org/en/latest/library/io.html)
- [`json` – JSON encoding and decoding](https://docs.micropython.org/en/latest/library/json.html)
- [`math` – mathematical functions](https://docs.micropython.org/en/latest/library/math.html)
- [`os` – basic “operating system” services](https://docs.micropython.org/en/latest/library/os.html)
- [`platform` – access to underlying platform’s identifying data](https://docs.micropython.org/en/latest/library/platform.html)
- [`random` – generate random numbers](https://docs.micropython.org/en/latest/library/random.html)
- [`re` – simple regular expressions](https://docs.micropython.org/en/latest/library/re.html)
- [`select` – wait for events on a set of streams](https://docs.micropython.org/en/latest/library/select.html)
- [`socket` – socket module](https://docs.micropython.org/en/latest/library/socket.html)
- [`ssl` – SSL/TLS module](https://docs.micropython.org/en/latest/library/ssl.html)
- [`struct` – pack and unpack primitive data types](https://docs.micropython.org/en/latest/library/struct.html)
- [`sys` – system specific functions](https://docs.micropython.org/en/latest/library/sys.html)
- [`time` – time related functions](https://docs.micropython.org/en/latest/library/time.html)
- [`zlib` – zlib compression & decompression](https://docs.micropython.org/en/latest/library/zlib.html)
- [`_thread` – multithreading support](https://docs.micropython.org/en/latest/library/_thread.html)
