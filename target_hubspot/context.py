from logging import Logger

from target_hubspot.model import TargetConfig


class JobContext:
    # We tend to pass a few objects around to most classes, so may as well standardize it properly w/ inheritance
    # Classes looking to use this simply have to inherit it and make a call to super().__init__(config=config, logger=logger)
    _config: TargetConfig
    _logger: Logger

    def __init__(self, config: TargetConfig, logger: Logger) -> None:
        self._config = config
        self._logger = logger
