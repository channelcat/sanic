from inspect import isclass
from os import environ
from pathlib import Path
from typing import Any, Union

from .utils import load_module_from_file_location, str_to_bool


SANIC_PREFIX = "SANIC_"
BASE_LOGO = """

                 Sanic
         Build Fast. Run Fast.

"""

DEFAULT_CONFIG = {
    "REQUEST_MAX_SIZE": 100000000,  # 100 megabytes
    "REQUEST_BUFFER_QUEUE_SIZE": 100,
    "REQUEST_BUFFER_SIZE": 65536,  # 64 KiB
    "REQUEST_TIMEOUT": 60,  # 60 seconds
    "RESPONSE_TIMEOUT": 60,  # 60 seconds
    "KEEP_ALIVE": True,
    "KEEP_ALIVE_TIMEOUT": 5,  # 5 seconds
    "WEBSOCKET_MAX_SIZE": 2 ** 20,  # 1 megabyte
    "WEBSOCKET_MAX_QUEUE": 32,
    "WEBSOCKET_READ_LIMIT": 2 ** 16,
    "WEBSOCKET_WRITE_LIMIT": 2 ** 16,
    "WEBSOCKET_PING_TIMEOUT": 20,
    "WEBSOCKET_PING_INTERVAL": 20,
    "GRACEFUL_SHUTDOWN_TIMEOUT": 15.0,  # 15 sec
    "ACCESS_LOG": True,
    "FORWARDED_SECRET": None,
    "REAL_IP_HEADER": None,
    "PROXIES_COUNT": None,
    "FORWARDED_FOR_HEADER": "X-Forwarded-For",
    "REQUEST_ID_HEADER": "X-Request-ID",
    "FALLBACK_ERROR_FORMAT": "html",
    "REGISTER": True,
}


class Config(dict):
    def __init__(self, defaults=None, load_env=True, keep_alive=None):
        defaults = defaults or {}
        super().__init__({**DEFAULT_CONFIG, **defaults})

        self.LOGO = BASE_LOGO

        if keep_alive is not None:
            self.KEEP_ALIVE = keep_alive

        if load_env:
            prefix = SANIC_PREFIX if load_env is True else load_env
            self.load_environment_vars(prefix=prefix)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as ke:
            raise AttributeError(f"Config has no '{ke.args[0]}'")

    def __setattr__(self, attr, value):
        self[attr] = value

    def load_environment_vars(self, prefix=SANIC_PREFIX):
        """
        Looks for prefixed environment variables and applies
        them to the configuration if present.
        """
        for k, v in environ.items():
            if k.startswith(prefix):
                _, config_key = k.split(prefix, 1)
                try:
                    self[config_key] = int(v)
                except ValueError:
                    try:
                        self[config_key] = float(v)
                    except ValueError:
                        try:
                            self[config_key] = str_to_bool(v)
                        except ValueError:
                            self[config_key] = v

    def update_config(self, config: Union[bytes, str, dict, Any]):
        """
        Update app.config.

        Note:: only upper case settings are considered.

        You can upload app config by providing path to py file
        holding settings.

        .. code-block:: python

            # /some/py/file
            A = 1
            B = 2

        .. code-block:: python

            config.update_config("${some}/py/file")

        Yes you can put environment variable here, but they must be provided
        in format: ${some_env_var}, and mark that $some_env_var is treated
        as plain string.

        You can upload app config by providing dict holding settings.

        .. code-block:: python

            d = {"A": 1, "B": 2}
            config.update_config(d)

        You can upload app config by providing any object holding settings,
        but in such case config.__dict__ will be used as dict holding settings.

        .. code-block:: python

            class C:
                A = 1
                B = 2

            config.update_config(C)
        """

        if isinstance(config, (bytes, str, Path)):
            config = load_module_from_file_location(location=config)

        if not isinstance(config, dict):
            cfg = {}
            if not isclass(config):
                cfg.update(
                    {
                        key: getattr(config, key)
                        for key in config.__class__.__dict__.keys()
                    }
                )

            config = dict(config.__dict__)
            config.update(cfg)

        config = dict(filter(lambda i: i[0].isupper(), config.items()))

        self.update(config)

    load = update_config
