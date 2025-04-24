# coding:utf-8

from os.path import join
from threading import Thread
from time import sleep
from typing import List

from xkits_file import Downloader

from xiaoya_downloader.alist import AListAPI
from xiaoya_downloader.resources import File
from xiaoya_downloader.resources import Resources


class Download():

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

    def download(self, file: File):
        file.update(-1)
        self.resources.save()

        if (downloader := Downloader(file.data, self.join(file))).start():
            # size: int = self.api.fs.get(join(file.path, file.name))["data"]["size"]  # noqa:E501
            file.update(downloader.stat.stat.st_size)
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
                        self.download(file)
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
