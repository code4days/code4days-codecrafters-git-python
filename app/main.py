import sys
import os
import zlib
import hashlib


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file":
        if sys.argv[2] == "-p":
            file_hash = sys.argv[3]
            with open(f".git/objects/{file_hash[:2]}/{file_hash[2:]}", "rb") as f:
                contents = zlib.decompress(f.read())
                print(contents.decode().split("\x00")[-1], end="")
        else:
            raise RuntimeError(f"Unknown option: {sys.argv[2]}")
    elif command == "hash-object":
        if sys.argv[2] == "-w":
            filename = sys.argv[3]
            file_contents = ""
            with open(filename, "r") as f:
                file_contents = f.read()

            hash_obj = f"blob {len(file_contents)}\0{file_contents}"
            file_hash = hashlib.sha1(hash_obj.encode()).hexdigest()
            os.mkdir(f".git/objects/{file_hash[:2]}")

            with open(f".git/objects/{file_hash[:2]}/{file_hash[2:]}", "wb") as f:
                f.write(zlib.compress(hash_obj.encode()))

            print(file_hash)
        else:
            raise RuntimeError(f"Unknown option: {sys.argv[2]}")

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
