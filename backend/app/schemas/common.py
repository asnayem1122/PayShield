"""Common schema types and validators."""

import re
from typing import Annotated
from pydantic import AfterValidator, BaseModel, Field

# Strict 2-decimal string format: 1-10 digits, period, exactly 2 digits (e.g. "1500.00")
DECIMAL_REGEX = re.compile(r"^\d{1,10}\.\d{2}$")


def validate_decimal_string(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("Amount must be transmitted as a string")
    v = v.strip()
    if not DECIMAL_REGEX.match(v):
        raise ValueError("Amount must be a decimal string with exactly two decimal places (e.g. '1500.00')")
    return v


DecimalString = Annotated[str, AfterValidator(validate_decimal_string)]


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
