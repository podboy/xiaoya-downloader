# coding:utf-8

from os import getenv
from typing import Optional
from typing import Sequence

from xkits_command import ArgParser
from xkits_command import Command
from xkits_command import CommandArgument
from xkits_command import CommandExecutor

from xiaoya_downloader.attribute import __description__
from xiaoya_downloader.attribute import __project__
from xiaoya_downloader.attribute import __urlhome__
from xiaoya_downloader.attribute import __version__
from xiaoya_downloader.webserver import run


@CommandArgument(__project__, description=__description__)
def add_cmd(_arg: ArgParser):  # pylint: disable=unused-argument
    pass


@CommandExecutor(add_cmd)
def run_cmd(cmds: Command) -> int:  # pylint: disable=unused-argument
    base_url: str = getenv("BASE_URL", "https://alist.xiaoya.pro/")
    base_dir: str = getenv("BASE_DIR", "data")
    host: str = getenv("HOST", "0.0.0.0")
    port: int = int(getenv("PORT", "5000"))
    debug: bool = getenv("DEBUG", "false").lower() == "true"
    run(base_url, base_dir, host, port, debug)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = Command()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv, epilog=f"For more, please visit {__urlhome__}.")  # noqa:E501
