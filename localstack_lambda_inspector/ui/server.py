import logging

from localstack.utils.run import ShellCommandThread
from localstack.utils.serving import Server
from localstack.utils.threads import FuncThread, TMP_THREADS

LOG = logging.getLogger(__name__)


class StreamlitApplicationServer(Server):
    app_path: str

    def __init__(
        self, app_path: str, port: int, host: str = "localhost", env: dict = None
    ):
        super().__init__(port, host)
        self.app_path = app_path
        self.env = env

    def do_start_thread(self) -> FuncThread:
        cmd = [
            "python",
            "-m",
            "streamlit",
            "run",
            self.app_path,
        ]
        env = {
            "STREAMLIT_SERVER_PORT": f"{self.port}",
            "STREAMLIT_GATHER_USAGE_STATS": "false",
        }

        if self.env:
            env.update(self.env)

        LOG.info("Starting Streamlit server: %s (env=%s)", cmd, env)
        t = ShellCommandThread(
            cmd,
            strip_color=True,
            log_listener=self._log_listener,
            env_vars=env,
        )
        TMP_THREADS.append(t)

        t.start()

        return t

    def _log_listener(self, line, **_kwargs):
        LOG.debug("[streamlit]: %s", line.rstrip())
