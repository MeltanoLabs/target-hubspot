from typing import Any, ClassVar, Dict

import pydantic
from pydantic import ConfigDict


class BaseConfig(pydantic.BaseModel):
    """
    Root class with sensible defaults that all domain Pydantic models should inherit from
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        use_enum_values=True,
        extra="allow"
    )

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        # We have lots of attributes prefixed by underscores for legacy reasons related to the Knex + Bookshelf JS libraries; accoridingly, we want to default to always dump by alias
        kwargs["by_alias"] = True
        return super().model_dump(*args, **kwargs)
