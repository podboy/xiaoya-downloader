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


def init(base_url: str, resources: Resources, locale: LocaleTemplate, fs_api: FS) -> Flask:  # noqa:E501
    app: Flask = Flask(__name__)

    @app.route("/search/resources/", methods=["GET"])
    def resources_search():
        keywords = request.args.get("keywords", "")
        queryurl = f"search?box={keywords}&url=&type=video"
        return redirect(urljoin(base_url, queryurl))

    @app.route("/download", defaults={"path": "/"}, methods=["GET"])
    @app.route("/download/", defaults={"path": "/"}, methods=["GET"])
    @app.route("/download/<path:path>", methods=["GET"])
    def download_list(path: str):
        data: List[Dict[str, Any]] = []
        path = path.strip("/")

        for file in resources[path]:
            item: Dict[str, Any] = {
                "name": file.name,
                "size": size if (size := file.size) > 0 else 0,
                "modified": file.modified,
                "optional": size >= 0,
                "target": "_blank",
                "href": urljoin(fs_api.base, join(path, file.name)),
            }

            data.append(item)

        for node in resources:
            if node.path.startswith(path) and node.path != path and len(node) > 0:  # noqa:E501
                optional: bool = True
                for file in node:
                    if file.size < 0:
                        optional = False
                        break

                item: Dict[str, Any] = {
                    "name": node.path.lstrip(path).strip("/"),
                    "size": node.size,
                    "optional": optional,
                    "target": "_self",
                    "href": join("/download", node.path)
                }

                data.append(item)

        return render_template(
            "table.html", data=data, origin=resources.base_url,
            parent=join("download", dirname(path) if path != "/" else ""),
            homepage="/download", submit_mode="delete",
            **locale.search(request.accept_languages.to_header(), "table").fill()  # noqa:E501
        )

    @app.route("/download", defaults={"path": "/"}, methods=["POST"])
    @app.route("/download/", defaults={"path": "/"}, methods=["POST"])
    @app.route("/download/<path:path>", methods=["POST"])
    def download_delete(path: str):
        items = loads(request.form["selected_items"])
        with resources.lock:
            for item in items:
                target: str = join(path, item)
                resources.remove(target)
            resources.save()
        return redirect(f"/download/{path}")

    @app.route("/resources", defaults={"path": "/"}, methods=["GET"])
    @app.route("/resources/", defaults={"path": "/"}, methods=["GET"])
    @app.route("/resources/<path:path>", methods=["GET"])
    def resources_list(path: str):
        data: List[Dict[str, Any]] = []

        for obj in fs_api.list(path):
            item: Dict[str, Any] = {
                "name": obj["name"],
                "size": obj["size"],
                "modified": obj["modified"],
            }

            if not obj["is_dir"]:
                item["href"] = urljoin(fs_api.base, join(path, obj["name"]))
                item["target"] = "_blank"
                item["optional"] = True
                if obj["name"] in (node := resources[path]):
                    if node[obj["name"]].size != 0:
                        item["optional"] = False
                    item["selected"] = True
            else:
                item["href"] = join("/resources", path.strip("/"), obj["name"])
                item["target"] = "_self"

            data.append(item)

        return render_template(
            "table.html", data=data, origin=resources.base_url,
            parent=join("resources", dirname(path) if path != "/" else ""),
            homepage="/resources", submit_mode="save",
            **locale.search(request.accept_languages.to_header(), "table").fill()  # noqa:E501
        )

    @app.route("/resources", defaults={"path": "/"}, methods=["POST"])
    @app.route("/resources/", defaults={"path": "/"}, methods=["POST"])
    @app.route("/resources/<path:path>", methods=["POST"])
    def resources_save(path: str):
        files = loads(request.form["selected_items"])
        with resources.lock:
            resources.submit_node(path, files)
            resources.save()
        return redirect(f"/resources/{path}")

    @app.route("/", methods=["GET"])
    def index():
        return redirect("/resources")

    return app


def run(  # pylint:disable=too-many-arguments,too-many-positional-arguments
        base_url: str, base_dir: str, api_url: str = "",
        host: str = "0.0.0.0", port: int = 5000, debug: bool = True):
    resources: Resources = Resources.load(api_url or base_url, base_dir)
    locale: LocaleTemplate = LocaleTemplate(dirname(__file__))
    Download.run(resources, fs_api := FS(api_url or base_url))
    app = init(base_url, resources, locale, fs_api)
    app.run(host=host, port=port, debug=debug)
