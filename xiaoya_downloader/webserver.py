# coding:utf-8

from json import loads
from os.path import dirname
from os.path import join
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import urljoin

from alist_kits import FS
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from xhtml.locale.template import LocaleTemplate

from xiaoya_downloader.download import Download
from xiaoya_downloader.resources import Resources


def init(resources: Resources, locale: LocaleTemplate, fs_api: FS) -> Flask:
    app: Flask = Flask(__name__)

    @app.route("/resources", defaults={"path": "/"}, methods=["GET"])
    @app.route("/resources/", defaults={"path": "/"}, methods=["GET"])
    @app.route("/resources/<path:path>", methods=["GET"])
    def resources_list(path: str):
        data: List[Dict[str, Any]] = []

        for obj in fs_api.list(path):
            item: Dict[str, Any] = {
                "name": obj["name"],
                "size": obj["size"],
                "is_dir": obj["is_dir"],
                "modified": obj["modified"],
            }

            if not obj["is_dir"]:
                if obj["name"] in (node := resources[path]):
                    if node[obj["name"]].size != 0:
                        item["protected"] = True
                    item["selected"] = True

            data.append(item)

        return render_template(
            "resources.html", base=urljoin(fs_api.base, path), data=data,
            parent=join("resources", dirname(path) if path != "/" else ""),
            homepage="/resources", submit_mode="save",
            **locale.search(request.accept_languages.to_header(), "resources").fill()  # noqa:E501
        )

    @app.route("/resources", defaults={"path": "/"}, methods=["POST"])
    @app.route("/resources/", defaults={"path": "/"}, methods=["POST"])
    @app.route("/resources/<path:path>", methods=["POST"])
    def resources_save(path: str):
        files = loads(request.form["selected_items"])
        resources.submit_node(path, files)
        resources.save()
        return redirect(urljoin(request.url_root, f"resources/{path}"))

    @app.route("/", methods=["GET"])
    def index():
        return redirect("/resources")

    return app


def run(base_url: str, base_dir: str, host: str = "0.0.0.0", port: int = 5000, debug: bool = True):  # noqa:E501
    resources: Resources = Resources.load(base_url, base_dir)
    locale: LocaleTemplate = LocaleTemplate(dirname(__file__))
    Download.run(resources, fs_api := FS(base_url))
    app = init(resources, locale, fs_api)
    app.run(host=host, port=port, debug=debug)
