import logging
import threading
from urllib.parse import urljoin

from rolo.websocket import WebSocketRequest, WebSocketDisconnectedError
from websockets import ConnectionClosed as UpstreamConnectionClosed
from websockets.sync.client import connect

LOG = logging.getLogger(__name__)


class WebsocketProxyHandler:
    """
    A dispatcher Handler which can be used in a ``Router[Handler]`` that proxies incoming websocket requests
    according to the configuration.

    The Handler is expected to be used together with a route that uses a ``path`` parameter named ``path`` in the URL.
    Fir example: if you want to forward all requests from ``/foobar/<path>`` to ``ws://localhost:8080/v1/<path>``,
    you would do the following::

        router = Router(dispatcher=handler_dispatcher())
        router.add("/foobar/<path:path>", WebsocketProxyHandler("ws://localhost:8080/v1", methods=["WEBSOCKET"])


    """

    def __init__(self, forward_base_url: str):
        self.forward_base_url = forward_base_url

    def __call__(self, request: WebSocketRequest, **kwargs):
        path = kwargs.get("path", "")
        forward_url = urljoin(self.forward_base_url, path)

        stopped = threading.Event()

        # connect to upstream
        with connect(forward_url) as upstream:
            # once connected to the upstream websocket, accept the incoming connection
            with request.accept() as incoming:

                def _pipe_to_upstream():
                    while not stopped.is_set():
                        try:
                            upstream.send(incoming.receive())
                        except (UpstreamConnectionClosed, WebSocketDisconnectedError):
                            stopped.set()

                def _pipe_to_downstream():
                    while not stopped.is_set():
                        try:
                            incoming.send(upstream.recv())
                        except (UpstreamConnectionClosed, WebSocketDisconnectedError):
                            stopped.set()

                # start thread that pipes incoming to upstream
                thread_upstream = threading.Thread(target=_pipe_to_upstream)
                thread_upstream.start()

                thread_downstream = threading.Thread(target=_pipe_to_downstream)
                thread_downstream.start()

                # wait until either thread exists, then this will return and close both connections through
                # the context managers
                stopped.wait()
