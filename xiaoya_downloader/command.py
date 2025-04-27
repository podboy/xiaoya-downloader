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
    _arg.add_argument("--debug-mode", type=bool, default=getenv("DEBUG_MODE", "false").lower() == "true")  # noqa:E501
    _arg.add_argument("--base-url", type=str, default=getenv("BASE_URL", "https://alist.xiaoya.pro/"))  # noqa:E501
    _arg.add_argument("--base-dir", type=str, default=getenv("BASE_DIR", "data"))  # noqa:E501
    _arg.add_argument("--api-url", type=str, default=getenv("API_URL", ""))
    _arg.add_argument("--host", type=str, default=getenv("HOST", "0.0.0.0"))
    _arg.add_argument("--port", type=int, default=int(getenv("PORT", "5000")))


@CommandExecutor(add_cmd)
def run_cmd(cmds: Command) -> int:  # pylint: disable=unused-argument
    debug_mode: bool = cmds.args.debug_mode
    base_url: str = cmds.args.base_url
    base_dir: str = cmds.args.base_dir
    api_url: str = cmds.args.api_url
    host: str = cmds.args.host
    port: int = cmds.args.port
    run(base_url, base_dir, api_url, host, port, debug_mode)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = Command()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv, epilog=f"For more, please visit {__urlhome__}.")  # noqa:E501
