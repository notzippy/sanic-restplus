# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sanic_restplus as restplus


async def post_json(client, url, data, status=200, **kwargs):
    response = await client.post(
        url, json=data, headers={"content-type": "application/json"}
    )
    assert response.status == status
    assert response.content_type == "application/json"

    return await response.json()


class PayloadTest(object):
    async def assert_errors(self, client, url, data, *errors):
        out = await post_json(client, url, data, status=400)
        assert "message" in out
        assert "errors" in out
        for error in errors:
            assert error in out["errors"]

    async def test_validation_false_on_constructor(self, app, client):
        api = restplus.Api(validate=False)

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        data = await post_json(client, "/validation/", {})
        assert data == {}

    async def test_validation_false_on_constructor_with_override(self, app, client):
        api = restplus.Api(validate=False)

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOn(restplus.Resource):
            @api.expect(fields, validate=True)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await self.assert_errors(client, "/validation/", {}, "name")

    async def test_validation_true_on_constructor(self, app, client):
        api = restplus.Api(validate=True)

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await self.assert_errors(client, "/validation/", {}, "name")

    async def test_validation_true_on_constructor_with_override(self, app, client):
        api = restplus.Api(validate=True)

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOff(restplus.Resource):
            @api.expect(fields, validate=False)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await self.assert_errors(client, "/validation/", {}, "name")

    def _setup_api_format_checker_tests(self, app, format_checker=None):
        class IPAddress(restplus.fields.Raw):
            __schema_type__ = "string"
            __schema_format__ = "ipv4"

        api = restplus.Api(format_checker=format_checker)
        model = api.model("MyModel", {"ip": IPAddress(required=True)})

        @api.route("/format_checker/")
        class TestResource(restplus.Resource):
            @api.expect(model, validate=True)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)

    async def test_format_checker_none_on_constructor(self, app, client):
        self._setup_api_format_checker_tests(app)

        out = await post_json(client, "/format_checker/", {"ip": "192.168.1"})
        assert out == {}

    async def test_format_checker_object_on_constructor(self, app, client):
        from jsonschema import FormatChecker

        self._setup_api_format_checker_tests(app, format_checker=FormatChecker())

        out = await post_json(
            client, "/format_checker/", {"ip": "192.168.1"}, status=400
        )
        assert "ipv4" in out["errors"]["ip"]

    async def test_validation_false_in_config(self, app, client):
        app.config["RESTPLUS_VALIDATE"] = False
        api = restplus.Api()

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        out = await post_json(client, "/validation/", {})
        assert out == {}

    async def test_validation_in_config(self, app, client):
        app.config["RESTPLUS_VALIDATE"] = True
        api = restplus.Api()

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOn(restplus.Resource):
            @api.expect(fields)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await self.assert_errors(client, "/validation/", {}, "name")

    async def test_api_payload(self, app, client):
        api = restplus.Api(validate=True)

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class Payload(restplus.Resource):
            payload = None

            @api.expect(fields)
            def post(self, request):
                Payload.payload = api.payload(request)
                return {}

        app.restplus_plugin.api(api)
        data = {"name": "John Doe", "age": 15}

        await post_json(client, "/validation/", data)
        assert Payload.payload == data

    async def test_validation_with_inheritance(self, app, client):
        """It should perform validation with inheritance (allOf/$ref)"""
        api = restplus.Api(validate=True)

        fields = api.model("Parent", {"name": restplus.fields.String(required=True)})

        child_fields = api.inherit("Child", fields, {"age": restplus.fields.Integer})

        @api.route("/validation/")
        class Inheritance(restplus.Resource):
            @api.expect(child_fields)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await post_json(client, "/validation/", {"name": "John Doe", "age": 15})

        await self.assert_errors(client, "/validation/", {"age": "15"}, "name", "age")

    async def test_validation_on_list(self, app, client):
        """It should perform validation on lists"""
        api = restplus.Api(validate=True)

        person = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer(required=True),
            },
        )

        family = api.model(
            "Family",
            {
                "name": restplus.fields.String(required=True),
                "members": restplus.fields.List(restplus.fields.Nested(person)),
            },
        )

        @api.route("/validation/")
        class List(restplus.Resource):
            @api.expect(family)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await self.assert_errors(
            client,
            "/validation/",
            {"name": "Doe", "members": [{"name": "Jonn"}, {"age": 42}]},
            "members.0.age",
            "members.1.name",
        )

    def _setup_expect_validation_single_resource_tests(self, app):
        # Setup a minimal Api with endpoint that expects in input payload
        # a single object of a resource
        api = restplus.Api(validate=True)

        user = api.model("User", {"username": restplus.fields.String()})

        @api.route("/validation/")
        class Users(restplus.Resource):
            @api.expect(user)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)

    def _setup_expect_validation_collection_resource_tests(self, app):
        # Setup a minimal Api with endpoint that expects in input payload
        # one or more objects of a resource
        api = restplus.Api(validate=True)

        user = api.model("User", {"username": restplus.fields.String()})

        @api.route("/validation/")
        class Users(restplus.Resource):
            @api.expect([user])
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)

    async def test_expect_validation_single_resource_success(self, app, client):
        self._setup_expect_validation_single_resource_tests(app)

        # Input payload is a valid JSON object
        out = await post_json(client, "/validation/", {"username": "alice"})
        assert {} == out

    async def test_expect_validation_single_resource_error(self, app, client):
        self._setup_expect_validation_single_resource_tests(app)

        # Input payload is an invalid JSON object
        await self.assert_errors(client, "/validation/", {"username": 123}, "username")

        # Input payload is a JSON array (expected JSON object)
        await self.assert_errors(client, "/validation/", [{"username": 123}], "")

    async def test_expect_validation_collection_resource_success(self, app, client):
        self._setup_expect_validation_collection_resource_tests(app)

        # Input payload is a valid JSON object
        out = await post_json(client, "/validation/", {"username": "alice"})
        assert {} == out

        # Input payload is a JSON array with valid JSON objects
        out = await post_json(
            client, "/validation/", [{"username": "alice"}, {"username": "bob"}]
        )
        assert {} == out

    async def test_expect_validation_collection_resource_error(self, app, client):
        self._setup_expect_validation_collection_resource_tests(app)

        # Input payload is an invalid JSON object
        await self.assert_errors(client, "/validation/", {"username": 123}, "username")

        # Input payload is a JSON array but with an invalid JSON object
        await self.assert_errors(
            client,
            "/validation/",
            [{"username": "alice"}, {"username": 123}],
            "username",
        )

    async def test_validation_with_propagate(self, app, client):
        app.config["PROPAGATE_EXCEPTIONS"] = True
        api = restplus.Api(validate=True)

        fields = api.model(
            "Person",
            {
                "name": restplus.fields.String(required=True),
                "age": restplus.fields.Integer,
                "birthdate": restplus.fields.DateTime,
            },
        )

        @api.route("/validation/")
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self, request):
                return {}

        app.restplus_plugin.api(api)
        await self.assert_errors(client, "/validation/", {}, "name")

    async def test_empty_payload(self, app, client):
        api = restplus.Api(validate=True)

        @api.route("/empty/")
        class Payload(restplus.Resource):
            def post(self, request):

                return {}

        app.restplus_plugin.api(api)
        response = await client.post(
            "/empty/", data="", headers={"content-type": "application/json"}
        )
        assert response.status == 200
