# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest

from sanic import Sanic, Blueprint
from sanic.testing import SanicTestClient
from spf import SanicPluginsFramework

from sanic_restplus.restplus import restplus as restplus_plugin
import sanic_restplus as restplus


class TestClient(SanicTestClient):
    def get_json(self, url, status=200, **kwargs):
        response = self.get(url, **kwargs)
        assert response.status_code == status
        assert response.content_type == "application/json"
        return json.loads(response.data.decode("utf8"))

    def post_json(self, url, data, status=200, **kwargs):
        response = self.post(
            url, data=json.dumps(data), headers={"content-type": "application/json"}
        )
        assert response.status_code == status
        assert response.content_type == "application/json"
        return json.loads(response.data.decode("utf8"))

    def get_specs(self, prefix="", status=200, **kwargs):
        """Get a Swagger specification for a RestPlus API"""
        return self.get_json("{0}/swagger.json".format(prefix), status=status, **kwargs)


@pytest.fixture
def app():
    app = Sanic(__name__)
    spf = SanicPluginsFramework(app)
    app.restplus_plugin = spf.register_plugin(restplus_plugin)
    app.test_client_class = TestClient
    yield app


@pytest.fixture
def client(app, loop, sanic_client):
    return loop.run_until_complete(sanic_client(app))


@pytest.fixture
def api(request, app):
    marker = request.keywords.get("api")
    bpkwargs = {}
    kwargs = {}
    if marker:
        if "prefix" in marker.kwargs:
            bpkwargs["url_prefix"] = marker.kwargs.pop("prefix")
        if "subdomain" in marker.kwargs:
            bpkwargs["subdomain"] = marker.kwargs.pop("subdomain")
        kwargs = marker.kwargs
    blueprint = Blueprint("api", __name__, **bpkwargs)
    api = restplus.Api(blueprint, **kwargs)
    app.register_blueprint(blueprint)
    yield api


@pytest.fixture(autouse=True)
def _push_custom_request_context(request):
    app = request.getfuncargvalue("app")
    options = request.keywords.get("request_context")

    if options is None:
        return

    ctx = app.test_request_context(*options.args, **options.kwargs)
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
