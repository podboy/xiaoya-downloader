# coding:utf-8

from json import dumps
from json import loads
from os import makedirs
from os import remove
from os import scandir
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import isdir
from os.path import isfile
from os.path import join
from shutil import rmtree
from threading import Lock
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from urllib.parse import urljoin


class File():  # pylint:disable=too-many-instance-attributes
    def __init__(self, base: str, path: str, name: str, size: int = 0, modified: str = ""):  # noqa:E501, pylint:disable=R0913,R0917
        self.__dirty: bool = False
        self.__modified: str = modified or self.timestamp()
        self.__data: str = urljoin(base, join("d", path, name))
        self.__link: str = urljoin(base, join(path, name))
        self.__base: str = base
        self.__path: str = path
        self.__name: str = name
        self.__size: int = size

    def __str__(self) -> str:
        return f"File(path={self.path}, name={self.name}, size={self.size})"

    @property
    def dirty(self) -> bool:
        return self.__dirty

    @property
    def modified(self) -> str:
        return self.__modified

    @property
    def base(self) -> str:
        return self.__base

    @property
    def path(self) -> str:
        return self.__path

    @property
    def name(self) -> str:
        return self.__name

    @property
    def size(self) -> int:
        return self.__size

    @property
    def link(self) -> str:
        return self.__link

    @property
    def data(self) -> str:
        return self.__data

    def update(self, size: int):
        self.__modified = self.timestamp()
        self.__dirty = True
        self.__size = size

    def remove(self, base_dir: str) -> bool:
        if self.size >= 0 and exists(path := join(base_dir, self.path, self.name)) and isfile(path):  # noqa:E501
            remove(path)
        return not exists(path)

    @classmethod
    def timestamp(cls) -> str:
        from datetime import datetime  # pylint:disable=import-outside-toplevel
        from datetime import timezone  # pylint:disable=import-outside-toplevel

        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")  # noqa:E501

    def dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "is_dir": False,
            "selected": True
        }

    def save(self) -> Dict[str, Any]:
        return {"name": self.name, "size": self.size, "modified": self.modified}  # noqa:E501

    @classmethod
    def load(cls, base: str, path: str, data: Dict[str, Any]) -> "File":
        return cls(base, path, data["name"], data.get("size", 0), data.get("modified", ""))  # noqa:E501


class Node():
    def __init__(self, base_url: str, base_dir: str, path: str):
        self.__files: Dict[str, File] = {}
        self.__dirty: bool = False
        self.__base_url: str = base_url
        self.__base_dir: str = base_dir
        self.__path: str = path

    def __str__(self) -> str:
        return f"Node({urljoin(self.base_url, self.path)})"

    def __len__(self) -> int:
        return len(self.__files)

    def __iter__(self) -> Iterator[File]:
        return iter(self.__files.values())

    def __getitem__(self, name: str) -> File:
        return self.__files[name]

    def __delitem__(self, name: str):
        if name in self.__files and self.__files[name].remove(self.base_dir):
            del self.__files[name]
            self.__dirty = True

    def __contains__(self, name: str) -> bool:
        return name in self.__files

    @property
    def dirty(self) -> bool:
        return self.__dirty or any(file.dirty for file in self)

    @property
    def base_url(self) -> str:
        return self.__base_url

    @property
    def base_dir(self) -> str:
        return self.__base_dir

    @property
    def path(self) -> str:
        return self.__path

    @property
    def size(self) -> int:
        return sum(file.size for file in self if file.size > 0)

    def reform(self):
        drop = [file.name for file in self if file.size == 0]
        for name in drop:
            del self.__files[name]
            self.__dirty = True

    def append(self, name: str):
        if name not in self.__files:
            file: File = File(self.base_url, self.path, name)
            self.__files.setdefault(name, file)
            self.__dirty = True

    def remove(self, name: str) -> bool:
        if name in self:
            del self[name]
        return name not in self

    def update(self, name: str, size: int):
        if (file := self.__files[name]).size != size:
            self.__dirty = True
            file.update(size)

    def dump(self) -> List[Dict[str, Any]]:
        return [file.dump() for file in self.__files.values()]

    def save(self, base_dir: str = "") -> bool:
        if self.dirty:  # pylint:disable=too-many-nested-blocks
            path: str = join(base_dir, self.path)

            if len(self.__files) > 0:
                if not exists(path):
                    makedirs(path)

                with open(file := f"{path}.json", "w", encoding="utf-8") as whdl:  # noqa:E501
                    data = [file.save() for file in self.__files.values()]
                    whdl.write(dumps(data))
            else:
                if exists(file := f"{path}.json"):
                    remove(file)

                if not exists(path) or (isdir(path) and not any(scandir(path))):  # noqa:E501
                    while path:
                        if exists(path):
                            if isdir(path) and not any(scandir(path)):
                                rmtree(path)
                            else:
                                break
                        path = dirname(path)
                    return False

        return True

    def load_file(self, data: Dict[str, Any]):
        if (file := File.load(self.base_url, self.path, data)).name not in self:  # noqa:E501
            self.__files.setdefault(file.name, file)

    @classmethod
    def load(cls, base_url: str, base_dir: str, path: str) -> "Node":
        file = join(base_dir, f"{path}.json")
        node = Node(base_url, base_dir, path)

        if exists(file) and isfile(file):
            with open(file, "r", encoding="utf-8") as rhdl:
                data: List[Dict[str, Any]] = loads(rhdl.read())
                for item in data:
                    node.load_file(item)

        return node


class Resources():
    FILE: str = "resources.json"

    def __init__(self, base_url: str, base_dir: str, nodes: Iterable[str] = []):  # noqa:E501, pylint:disable=W0102
        self.__nodes: Dict[str, Node] = {}
        self.__files: List[File] = []
        for path in nodes:
            node = Node.load(base_url, base_dir, path)
            self.__nodes[path] = node
            self.__files.extend(node)
        self.__base_url: str = base_url
        self.__base_dir: str = base_dir
        self.__dirty: bool = False
        self.__lock: Lock = Lock()

    def __len__(self) -> int:
        return len(self.__nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__nodes.values())

    def __getitem__(self, path: str) -> Node:
        if (name := path.strip("/")) not in self.__nodes:
            self.__nodes[name] = Node(self.base_url, self.base_dir, name)
            self.__dirty = True
        return self.__nodes[name]

    def __delitem__(self, path: str):
        if (name := path.strip("/")) in self.__nodes:
            node = self.__nodes[name]
            files = [item.name for item in node]
            for file in files:
                del node[file]

            if len(node) == 0 and exists(path := join(node.base_dir, node.path)) and isdir(path) and not any(scandir(path)):  # noqa:E501
                rmtree(path)

            if not exists(path):
                del self.__nodes[name]
                self.__dirty = True

    def __contains__(self, path: str) -> bool:
        return path.strip("/") in self.__nodes

    @property
    def base_url(self) -> str:
        return self.__base_url

    @property
    def base_dir(self) -> str:
        return self.__base_dir

    @property
    def dirty(self) -> bool:
        return self.__dirty

    @property
    def lock(self) -> Lock:
        return self.__lock

    @property
    def files(self) -> List[File]:
        return self.__files

    def remove(self, path: str) -> bool:
        if path in self:
            del self[path]
            return path not in self

        if (parent := dirname(path)) in self:
            if not (node := self[parent]).remove(basename(path)):
                return False
            if len(node) == 0:
                del self[node.path]
        return True

    def dump(self) -> Dict[str, List[Dict[str, Any]]]:
        return {node.path: node.dump() for node in self.__nodes.values() if len(node) > 0}  # noqa:E501

    def save(self, base_dir: Optional[str] = None):
        base: str = base_dir if base_dir is not None else self.base_dir
        drop: List[Node] = []

        for node in self:
            if not node.save(base):
                drop.append(node)

        for node in drop:
            del self[node.path]

        if self.__dirty:
            config: str = join(base, self.FILE)
            with open(config, "w", encoding="utf-8") as whdl:
                whdl.write(dumps([node.path for node in self]))
                self.__dirty = False

        files: List[File] = []
        for node in self:
            files.extend(node)
        self.__files = files

    @classmethod
    def load(cls, base_url: str, base_dir: str) -> "Resources":
        config: str = join(base_dir, cls.FILE)
        if exists(config) and isfile(config):
            with open(config, "r", encoding="utf-8") as rhdl:
                data: List[str] = loads(rhdl.read())
                return cls(base_url, base_dir, data)
        return cls(base_url, base_dir)

    def submit_node(self, path, files: Iterable[str]):
        self[path].reform()
        for name in files:
            self[path].append(name)

    def submit_file(self, path, name: str, size: int):
        return self[path].update(name, size)
