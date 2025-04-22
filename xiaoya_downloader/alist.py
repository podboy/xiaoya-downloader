# coding:utf-8

from typing import Dict
from urllib.parse import urljoin


def send_post_request(url: str, data: Dict):
    from requests import post  # pylint:disable=import-outside-toplevel

    response = post(url, json=data, timeout=180.0)
    response.raise_for_status()
    return response


class AListAPI:
    class FS:  # pylint:disable=too-few-public-methods
        def __init__(self, base_url: str):
            self.__base_url = base_url

        def list(self, path: str = "/") -> Dict:
            url = urljoin(self.__base_url, "/api/fs/list")
            data = {
                "path": path,
                "password": "",
                "page": 1,
                "per_page": 0,
                "refresh": False
            }
            return send_post_request(url, data).json()

    def __init__(self, base_url: str):
        self.__fs = AListAPI.FS(base_url)
        self.__base_url = base_url

    @property
    def base_url(self) -> str:
        return self.__base_url

    @property
    def fs(self) -> "AListAPI.FS":
        return self.__fs
