# coding:utf-8

from os import remove
from os.path import exists
from os.path import isfile
from os.path import join
from threading import Thread
from time import sleep

from alist_kits import FS
from xkits_file import Downloader
from xkits_file import FileStat
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

    def download(self, file: File) -> bool:
        expected_size: int = self.fs_api.get(join(file.path, file.name))["size"]  # noqa:E501
        assert isinstance(expected_size, int), f"Unexpected type '{type(expected_size)}'"  # noqa:E501
        downloader: Downloader = Downloader(file.data, self.join(file))

        if not exists(downloader.path):
            with self.resources.lock:
                file.update(-expected_size)
                self.resources.save()

            if not downloader.start():
                Logger.stdout_red(f"Failed to download {join(file.path, file.name)}")  # noqa:E501
                return False

        if not isfile(downloader.path):
            Logger.stdout_red(f"Path '{downloader.path}' is not a regular file")  # noqa:E501
            return False

        if (actual_size := downloader.stat.stat.st_size) != expected_size:
            Logger.stdout_red(f"Path '{downloader.path}' expected size {expected_size} != {actual_size}")  # noqa:E501
            remove(downloader.path)
            return False

        with self.resources.lock:
            file.update(expected_size)
            self.resources.save()
        return True

    def execute(self, file: File) -> bool:
        path: str = self.join(file)

        if file.size <= 0 or not exists(path):
            try:
                if not self.download(file):
                    return False
            except Exception as e:  # pylint:disable=broad-exception-caught
                Logger.stdout_red(f"Failed to download '{join(file.path, file.name)}': {e}")  # noqa:E501
                return False

        if file.size <= 0:
            Logger.stdout_red(f"'{join(file.path, file.name)}' unexpected size '{file.size}'")  # noqa:E501
            return False

        if not exists(path) or not isfile(path):
            Logger.stdout_red(f"Path '{path}' is not a regular file")  # noqa:E501
            return False

        if (stat := FileStat(path)).stat.st_size != file.size:
            Logger.stdout_red(f"Path '{path}' expected size {file.size} != {stat.stat.st_size}")  # noqa:E501
            remove(path)
            return False

        return True

    def daemon(self):
        delay: float = 15.0

        while True:
            try:
                if len(self.resources.files) > 0:
                    with self.resources.lock:
                        file = self.resources.files.pop(0)
                    if not self.execute(file):
                        self.resources.files.append(file)
                    delay = max(1.0, delay * 0.9)
                else:
                    delay = min(delay * 1.1, 180.0)
            except Exception:  # pylint:disable=broad-exception-caught
                import traceback  # pylint:disable=import-outside-toplevel

                traceback.print_exc()
                delay = min(delay * 1.5, 180.0)
            finally:
                sleep(delay)

    @classmethod
    def run(cls, resources: Resources, fs_api: FS):
        Thread(target=cls(resources, fs_api).daemon).start()
