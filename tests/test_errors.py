# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest

# from flask import Blueprint, abort
# from flask.signals import got_request_exception

# from werkzeug.exceptions import HTTPException, BadRequest, NotFound, Aborter
# from werkzeug.http import quote_etag, unquote_etag

import sanic.exceptions
from sanic.exceptions import SanicException, NotFound, InvalidUsage
import sanic_restplus as restplus


class ErrorsTest(object):
    SANIC_DEFAULT_MEDIATYPE = "text/plain; charset=utf-8"

    def test_abort_type(self):
        with pytest.raises(NotFound):
            restplus.abort(404)

    def test_abort_no_data(self):
        with pytest.raises(NotFound) as cm:
            restplus.abort(404)
        assert not hasattr(cm.value, "data")

    def test_abort_data(self):
        with pytest.raises(NotFound) as cm:
            restplus.abort(404, foo="bar")
        assert cm.value.data == {"foo": "bar"}

    def test_abort_custom_message(self):
        with pytest.raises(NotFound) as cm:
            restplus.abort(404, "My message")
        assert cm.value.data["message"] == "My message"

    async def test_abort_code_only_with_defaults(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                api.abort(403)

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 403
        assert response.content_type == "application/json"
        assert response.headers["Content-Type"] == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_abort_with_message(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                api.abort(403, "A message")

        # TODO: Use eager-init pattern with this test when it is implemented in sanic-restplus
        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 403
        assert response.content_type == "application/json"

        data = await response.json()
        assert data["message"] == "A message"

    async def test_abort_with_lazy_init(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                api.abort(403)

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 403
        assert response.content_type == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_abort_on_exception(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise ValueError()

        # TODO: Use eager-init pattern with this test when it is implemented in sanic-restplus
        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 500
        assert response.content_type == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_abort_on_exception_with_lazy_init(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise ValueError()

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 500
        assert response.content_type == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_errorhandler_for_custom_exception(self, app, client):
        api = restplus.Api()

        class CustomException(RuntimeError):
            pass

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise CustomException("error")

        @api.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {"message": str(error), "test": "value"}, 400

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 400
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": "error", "test": "value"}

    async def test_errorhandler_for_custom_exception_with_headers(self, app, client):
        api = restplus.Api()

        class CustomException(RuntimeError):
            pass

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise CustomException("error")

        @api.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {"message": "some maintenance"}, 503, {"Retry-After": 120}

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 503
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": "some maintenance"}
        assert response.headers["Retry-After"] == "120"

    async def test_errorhandler_for_httpexception(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise InvalidUsage("Testing")

        @api.errorhandler(InvalidUsage)
        def handle_badrequest_exception(error):
            return {"message": str(error), "test": "value"}, 400

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 400
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": str(InvalidUsage("Testing")), "test": "value"}

    async def test_errorhandler_with_namespace(self, app, client):
        api = restplus.Api()

        ns = restplus.Namespace("ExceptionHandler", path="/")

        class CustomException(RuntimeError):
            pass

        @ns.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise CustomException("error")

        @ns.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {"message": str(error), "test": "value"}, 400

        api.add_namespace(ns)

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 400
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": "error", "test": "value"}

    async def test_default_errorhandler(self, app, client):
        api = restplus.Api()

        @api.route("/test/")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise Exception("error")

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 500
        assert response.content_type == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_default_errorhandler_with_propagate_true(self, app, client):
        blueprint = Blueprint("api", __name__, url_prefix="/api")
        api = restplus.Api(blueprint)

        @api.route("/test/")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise Exception("error")

        app.register_blueprint(blueprint)

        app.config["PROPAGATE_EXCEPTIONS"] = True

        response = await client.get("/api/test/")
        assert response.status == 500
        assert response.content_type == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_custom_default_errorhandler(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise Exception("error")

        @api.errorhandler
        def default_error_handler(error):
            return {"message": str(error), "test": "value"}, 500

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 500
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": "error", "test": "value"}

    async def test_custom_default_errorhandler_with_headers(self, app, client):
        api = restplus.Api()

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise Exception("error")

        @api.errorhandler
        def default_error_handler(error):
            return {"message": "some maintenance"}, 503, {"Retry-After": 120}

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 503
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": "some maintenance"}
        assert response.headers["Retry-After"] == "120"

    async def test_errorhandler_lazy(self, app, client):
        api = restplus.Api()

        class CustomException(RuntimeError):
            pass

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                raise CustomException("error")

        @api.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {"message": str(error), "test": "value"}, 400

        app.restplus_plugin.api(api)
        response = await client.get("/test/")
        assert response.status == 400
        assert response.content_type == "application/json"

        data = await response.json()
        assert data == {"message": "error", "test": "value"}

    async def test_handle_api_error(self, app, client):
        api = restplus.Api()

        @api.route("/api", endpoint="api")
        class Test(restplus.Resource):
            def get(self, request):
                api.abort(404)

        app.restplus_plugin.api(api)
        response = await client.get("/api")
        assert response.status == 404
        assert response.headers["Content-Type"] == "application/json"

        data = await response.json()
        assert "message" in data

    async def test_handle_non_api_error(self, app, client):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        response = await client.get("/foo")
        assert response.status == 404

        assert response.headers["Content-Type"] == api.default_mediatype

    async def test_non_api_error_404_catchall(self, app, client):
        api = restplus.Api(catch_all_404s=True)

        app.restplus_plugin.api(api)
        response = await client.get("/foo")
        assert response.headers["Content-Type"] == api.default_mediatype

    async def test_handle_error_signal(self, app):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        exception = InvalidUsage("Testing")

        recorded = []

        def record(sender, exception):
            recorded.append(exception)

        got_request_exception.connect(record, app)
        try:
            # with self.app.test_request_context("/foo"):
            api.handle_error(exception)
            assert len(recorded) == 1
            assert exception is recorded[0]
        finally:
            got_request_exception.disconnect(record, app)

    async def test_handle_error(self, app):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        response = api.handle_error(InvalidUsage("Testing"))
        assert response.status == 400

        data = await response.json()
        assert data == {"message": InvalidUsage.description}

    async def test_handle_error_does_not_duplicate_content_length(self, app):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        # with self.app.test_request_context("/foo"):
        response = api.handle_error(InvalidUsage("Testing"))
        assert len(response.headers.getlist("Content-Length")) == 1

    async def test_handle_smart_errors(self, app):
        api = restplus.Api()
        view = restplus.Resource

        api.add_resource(view, "/foo", endpoint="bor")
        api.add_resource(view, "/fee", endpoint="bir")
        api.add_resource(view, "/fii", endpoint="ber")

        with app.test_request_context("/faaaaa"):
            response = api.handle_error(NotFound())
            assert response.status == 404

            data = await response.json()
            assert data == {"message": NotFound.description}

        with app.test_request_context("/fOo"):
            response = api.handle_error(NotFound())
            assert response.status == 404

            data = await response.text()
            assert "did you mean /foo ?" in data

        app.config["ERROR_404_HELP"] = False

        app.restplus_plugin.api(api)
        response = api.handle_error(NotFound())
        assert response.status == 404

        data = await response.json()
        assert data == {"message": NotFound.description}

    async def test_error_router_falls_back_to_original(self, app, mocker):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        app.handle_exception = mocker.Mock()
        api.handle_error = mocker.Mock(side_effect=Exception())
        api._has_fr_route = mocker.Mock(return_value=True)
        exception = mocker.Mock(spec=SanicException)

        api.error_router(app.handle_exception, exception)

        app.handle_exception.assert_called_with(exception)

    async def test_fr_405(self, app, client):
        api = restplus.Api()

        @api.route("/ids/<id>", endpoint="hello")
        class HelloWorld(restplus.Resource):
            def get(self, request):
                return {}

        app.restplus_plugin.api(api)
        response = await client.post("/ids/3")
        assert response.status == 405
        assert response.content_type == api.default_mediatype
        # Allow can be of the form 'GET, PUT, POST'
        import ipdb

        ipdb.set_trace()
        allow = ", ".join(set(response.headers.get_all("Allow")))
        allow = set(method.strip() for method in allow.split(","))
        assert allow == set(["HEAD", "OPTIONS", "GET"])

    @pytest.mark.options(debug=True)
    async def test_exception_header_forwarded(self, app, client):
        """Ensure that HTTPException's headers are extended properly"""
        api = restplus.Api()

        class NotModified(SanicException):
            status_code = 304

            def __init__(self, etag, *args, **kwargs):
                super(NotModified, self).__init__(*args, **kwargs)
                self.etag = quote_etag(etag)

            def get_headers(self, *args, **kwargs):
                return [("ETag", self.etag)]

        custom_abort = Aborter(mapping={304: NotModified})

        @api.route("/foo")
        class Foo1(restplus.Resource):
            def get(self, request):
                custom_abort(304, etag="myETag")

        app.restplus_plugin.api(api)
        foo = await client.get("/foo")
        assert foo.get_etag() == unquote_etag(quote_etag("myETag"))

    async def test_handle_server_error(self, app):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        response = api.handle_error(Exception())
        assert response.status == 500

        data = await response.json()
        assert data == {"message": "Internal Server Error"}

    async def test_handle_error_with_code(self, app):
        api = restplus.Api(serve_challenge_on_401=True)
        app.restplus_plugin.api(api)

        exception = Exception()
        exception.code = "Not an integer"
        exception.data = {"foo": "bar"}

        response = api.handle_error(exception)
        assert response.status == 500

        data = await response.json()
        assert data == {"foo": "bar"}

    async def test_errorhandler_swagger_doc(self, app, client):
        api = restplus.Api()
        app.restplus_plugin.api(api)

        class CustomException(RuntimeError):
            pass

        error = api.model("Error", {"message": restplus.fields.String()})

        @api.route("/test/", endpoint="test")
        class TestResource(restplus.Resource):
            def get(self, request):
                """
                Do something

                :raises CustomException: In case of something
                """
                pass

        @api.errorhandler(CustomException)
        @api.header("Custom-Header", "Some custom header")
        @api.marshal_with(error, code=503)
        def handle_custom_exception(error):
            """Some description"""
            pass

        specs = client.get_specs()

        assert "Error" in specs["definitions"]
        assert "CustomException" in specs["responses"]

        response = specs["responses"]["CustomException"]
        assert response["description"] == "Some description"
        assert response["schema"] == {"$ref": "#/definitions/Error"}
        assert response["headers"] == {
            "Custom-Header": {"description": "Some custom header", "type": "string"}
        }

        operation = specs["paths"]["/test/"]["get"]
        assert "responses" in operation
        assert operation["responses"] == {
            "503": {"$ref": "#/responses/CustomException"}
        }
