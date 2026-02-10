import logging

from localstack import config, constants
from localstack.extensions.api import Extension, http
from localstack.utils import net
from localstack.utils.serving import Server
from localstack.utils.urls import localstack_host
from rolo.proxy import ProxyHandler

LOG = logging.getLogger(__name__)


class LocalstackLambdaInspector(Extension):
    name = "localstack-lambda-inspector"
    hostname_prefix = "lambda-inspector."

    server: Server | None

    def __init__(self):
        self.server = None

    def on_extension_load(self):
        # TODO: logging should be configured automatically for extensions
        from localstack.aws.handlers import cors

        if config.DEBUG:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.getLogger("localstack_lambda_inspector").setLevel(level=level)

        cors.ALLOWED_CORS_ORIGINS.append(self.get_url())

    def on_platform_start(self):
        # this will apply patches directly
        from . import patches  # noqa
        from localstack_lambda_inspector.ui.server import StreamlitApplicationServer
        from localstack_lambda_inspector.ui import streamlit_app

        self.server = StreamlitApplicationServer(
            streamlit_app.__file__,
            port=net.get_free_tcp_port(),
        )
        LOG.info(
            "starting Localstack Lambda Inspector UI at %s (serving %s)",
            self.server.url,
            streamlit_app.__file__,
        )
        self.server.start()

        LOG.debug("adding allowed CORS origin %s", self.get_url())

    def get_localstack_url(self) -> str:
        return f"{constants.LOCALHOST_HOSTNAME}:{localstack_host().port}"

    def get_url(self):
        url = f"http://{self.hostname_prefix}{self.get_localstack_url()}"
        return url

    def on_platform_shutdown(self):
        if self.server:
            self.server.shutdown()

    def on_platform_ready(self):
        LOG.info("serving lambda-inspector extension on host: %s", self.get_url())

    def update_gateway_routes(self, router: http.Router[http.RouteHandler]):
        # add the API to the router
        from localstack_lambda_inspector.api import Api
        from localstack_lambda_inspector.ws import WebsocketProxyHandler

        router.add(Api())

        proxy = ProxyHandler(self.server.url)

        router.add(
            "/",
            host=f"{self.hostname_prefix}<host>",
            endpoint=proxy,
            methods=["GET", "POST", "PATCH", "OPTIONS", "DELETE"],
        )
        router.add(
            "/<path:path>",
            host=f"{self.hostname_prefix}<host>",
            endpoint=proxy,
            methods=["GET", "POST", "PATCH", "OPTIONS", "DELETE"],
        )

        ws_url = "ws://" + self.server.url.removeprefix("http://").removeprefix(
            "https://"
        )
        ws_proxy = WebsocketProxyHandler(ws_url)
        router.add(
            "/",
            host=f"{self.hostname_prefix}<host>",
            endpoint=ws_proxy,
            methods=["WEBSOCKET"],
        )
        router.add(
            "/<path:path>",
            host=f"{self.hostname_prefix}<host>",
            endpoint=ws_proxy,
            methods=["WEBSOCKET"],
        )
