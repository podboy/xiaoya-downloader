# coding:utf-8

from os.path import join
from threading import Thread
from time import sleep
from typing import List

from xiaoya_downloader.resources import File
from xiaoya_downloader.resources import Resources


class Download():
    CHUNK_SIZE: int = 1048576

    def __init__(self, resources: Resources):
        self.__resources: Resources = resources

    @property
    def resources(self) -> Resources:
        return self.__resources

    def join(self, file: File) -> str:
        return join(self.resources.base_dir, file.path, file.name)

    def handle(self, file: File):
        from requests import get  # pylint:disable=import-outside-toplevel

        with get(file.data, stream=True, timeout=180.0) as stream:
            with open(self.join(file), "wb", encoding="utf-8") as whdl:
                file.update(-1)
                self.resources.save()
                for chunk in stream.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:
                        whdl.write(chunk)
                file.update(whdl.tell())
                self.resources.save()

    def daemon(self):
        while True:
            try:
                todo: List[File] = []

                for node in self.resources:
                    for file in node:
                        if file.size <= 0:
                            todo.append(file)

                if len(todo) > 0:
                    for file in todo:
                        self.handle(file)
                    todo.clear()

            except Exception:  # pylint:disable=broad-exception-caught
                import traceback  # pylint:disable=import-outside-toplevel

                traceback.print_exc()
            finally:
                sleep(3.0)

    @classmethod
    def run(cls, resources: Resources):
        Thread(target=cls(resources).daemon).start()
