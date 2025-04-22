# coding:utf-8

from json import loads
from os.path import dirname
from os.path import join
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import urljoin

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from xhtml.locale.template import LocaleTemplate

from xiaoya_downloader.alist import AListAPI
from xiaoya_downloader.download import Download
from xiaoya_downloader.resources import Resources


def init(resources: Resources, locale: LocaleTemplate, api: AListAPI) -> Flask:
    app: Flask = Flask(__name__)

    @app.route("/resources", defaults={"path": "/"}, methods=["GET"])
    @app.route("/resources/", defaults={"path": "/"}, methods=["GET"])
    @app.route("/resources/<path:path>", methods=["GET"])
    def resources_list(path: str):
        response = api.fs.list(path)
        if response.get("code") != 200:
            return "Not Found", 404

        base = urljoin(api.base_url, path)
        data: List[Dict[str, Any]] = response.get(
            "data", {}).get("content", [])
        for item in data:
            if not item["is_dir"]:
                if item["name"] in (node := resources[path]):
                    if node[item["name"]].size != 0:
                        item["protected"] = True
                    item["selected"] = True
        parent = join("resources", dirname(path) if path != "/" else "")

        return render_template(
            "resources.html", base=base, data=data, parent=parent,
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


def run(base_url: str, base_dir: str):
    resources: Resources = Resources.load(base_url, base_dir)
    locale: LocaleTemplate = LocaleTemplate(dirname(__file__))
    api: AListAPI = AListAPI(base_url)
    app = init(resources, locale, api)
    Download.run(resources)
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    run("http://xiaoya.lxc:5678/", "data")
