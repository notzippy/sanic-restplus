from sanic import Sanic
from sanic_restplus.restplus import restplus
from sanic_plugin_toolkit import SanicPluginRealm
from examples.zoo import api

app = Sanic(__name__)
realm = SanicPluginRealm(app)
rest_assoc = realm.register_plugin(restplus)
rest_assoc.api(api)

app.run(debug=True, auto_reload=False)
