from logging import Logger

from target_hubspot.constants import TargetConfig


class ConfigInheriter:
    # We tend to pass a few objects around to most classes, so may as well standardize it properly w/ inheritance
    _config: TargetConfig
    _logger: Logger

    def __init__(self, config: TargetConfig, logger: Logger) -> None:
        self._config = config
        self._logger = logger
