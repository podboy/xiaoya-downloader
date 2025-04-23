# coding:utf-8

from os.path import join
from threading import Thread
from time import sleep
from typing import List

from xkits_logger import Logger

from xiaoya_downloader.alist import AListAPI
from xiaoya_downloader.resources import File
from xiaoya_downloader.resources import Resources


class Download():
    CHUNK_SIZE: int = 1048576

    def __init__(self, resources: Resources, api: AListAPI):
        self.__resources: Resources = resources
        self.__api: AListAPI = api

    @property
    def resources(self) -> Resources:
        return self.__resources

    @property
    def api(self) -> AListAPI:
        return self.__api

    def join(self, file: File) -> str:
        return join(self.resources.base_dir, file.path, file.name)

    def handle(self, file: File):
        from requests import get  # pylint:disable=import-outside-toplevel

        with get(file.data, stream=True, timeout=180.0) as stream:
            stream.raise_for_status()  # HTTPError
            with open(path := self.join(file), "wb") as whdl:
                file.update(-1)
                self.resources.save()
                Logger.stdout(f"Download {path} started")
                for chunk in stream.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:
                        whdl.write(chunk)
                size: int = self.api.fs.get(join(file.path, file.name))["data"]["size"]  # noqa:E501
                if whdl.tell() == size:
                    Logger.stdout_green(
                        f"Download {path} size {size} fininshed")
                    file.update(size)
                else:
                    Logger.stderr_red(f"Download {path} size {size} error")
                    file.update(-size)
                self.resources.save()

    def daemon(self):
        delay: float = 15.0

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

                delay = max(5.0, delay * 0.9)
            except Exception:  # pylint:disable=broad-exception-caught
                import traceback  # pylint:disable=import-outside-toplevel

                traceback.print_exc()
                delay = min(delay * 1.5, 180.0)
            finally:
                sleep(delay)

    @classmethod
    def run(cls, resources: Resources, api: AListAPI):
        Thread(target=cls(resources, api).daemon).start()
