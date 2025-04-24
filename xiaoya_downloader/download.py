# coding:utf-8

from os.path import join
from threading import Thread
from time import sleep

from alist_kits import FS
from xkits_file import Downloader
from xkits_logger import Logger

from xiaoya_downloader.resources import File
from xiaoya_downloader.resources import Resources


class Download():

    def __init__(self, resources: Resources, fs_api: FS):
        self.__resources: Resources = resources
        self.__fs_api: FS = fs_api

    @property
    def resources(self) -> Resources:
        return self.__resources

    @property
    def fs_api(self) -> FS:
        return self.__fs_api

    def join(self, file: File) -> str:
        return join(self.resources.base_dir, file.path, file.name)

    def download(self, file: File):
        file.update(-(size := self.fs_api.get(join(file.path, file.name))["size"]))  # noqa:E501
        self.resources.save()

        if (downloader := Downloader(file.data, self.join(file))).start():
            if (file_size := downloader.stat.stat.st_size) == size:
                file.update(file_size)
                self.resources.save()
            else:
                Logger.stderr_red(f"Failed to download {file.name}, expected size {size} != {file_size}")  # noqa:E501

    def daemon(self):
        delay: float = 15.0

        while True:
            try:
                for node in self.resources:
                    for file in node:
                        if file.size <= 0:
                            self.download(file)
                delay = max(5.0, delay * 0.9)
            except Exception:  # pylint:disable=broad-exception-caught
                import traceback  # pylint:disable=import-outside-toplevel

                traceback.print_exc()
                delay = min(delay * 1.5, 180.0)
            finally:
                sleep(delay)

    @classmethod
    def run(cls, resources: Resources, fs_api: FS):
        Thread(target=cls(resources, fs_api).daemon).start()
