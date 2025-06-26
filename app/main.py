from __future__ import annotations
import sys
import os
import zlib
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TreeEntry:
    mode: int
    name: str
    hash: bytes

    def as_bytes(self) -> bytes:
        return f"{self.mode} {self.name}\0".encode() + self.hash


def create_hash(data: bytes, obj_type: str) -> hashlib._Hash:
    header = f"{obj_type} {len(data)}\0".encode()
    full_data = header + data
    sha1 = hashlib.sha1(full_data)
    file_hash = sha1.hexdigest()

    path = Path(".git/objects") / file_hash[:2] / file_hash[2:]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(str(path), "wb") as f:
            f.write(zlib.compress(full_data))
    return sha1


def write_tree(start_dir: str) -> hashlib._Hash:
    start_dir = Path(start_dir)
    tree_entries: list[bytes] = []
    for entry in start_dir.iterdir():
        if str(entry) == ".git":
            continue

        if entry.is_dir():
            tree_hash = write_tree(entry)
            tree_entry = TreeEntry(mode=40000, name=entry.name, hash=tree_hash.digest())
            tree_entries.append(tree_entry)

        if entry.is_file():
            file_hash = create_hash(open(entry, "rb").read(), "blob")
            tree_entry = TreeEntry(
                mode=100644, name=entry.name, hash=file_hash.digest()
            )
            tree_entries.append(tree_entry)

    tree_hash = create_hash(
        b"".join(
            tree_entry.as_bytes()
            for tree_entry in sorted(tree_entries, key=lambda item: item.name)
        ),
        "tree",
    )
    return tree_hash


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

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
            file_hash = create_hash(open(filename, "rb").read(), "blob")

            print(file_hash.hexdigest())
        else:
            raise RuntimeError(f"Unknown option: {sys.argv[2]}")
    elif command == "ls-tree":
        if sys.argv[2] == "--name-only":
            tree_sha = sys.argv[3]
            with open(f".git/objects/{tree_sha[:2]}/{tree_sha[2:]}", "rb") as f:
                tree_obj = zlib.decompress(f.read())
                _, tree_obj_data = tree_obj.split(b"\x00", maxsplit=1)

                while tree_obj_data:
                    mode_name, tree_obj_data = tree_obj_data.split(b"\x00", maxsplit=1)
                    mode, name = mode_name.split()
                    print(name.decode())
                    tree_obj_data = tree_obj_data[20:]
    elif command == "write-tree":
        start_dir = "."
        tree_hash = write_tree(start_dir)
        print(tree_hash.hexdigest())

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
