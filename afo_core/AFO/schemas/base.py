# Trinity Score: 90.0 (Established by Chancellor)
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """AFO Kingdom Base Schema (眞/善)
    - Enforces extra="forbid" to prevent data pollution
    - Validates default values
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
        strict=True,
    )
