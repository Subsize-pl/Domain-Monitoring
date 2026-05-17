from pydantic import ValidationError


def map_validation_errors(
    exc: ValidationError,
    *,
    prefix: str,
) -> dict[str, str]:
    mapped: dict[str, str] = {}

    for error in exc.errors():
        loc = error.get("loc", ())
        key = str(loc[-1]) if loc else "form"

        if key in {"__root__", "form"}:
            mapped[f"{prefix}_form"] = error["msg"]
            continue

        mapped[f"{prefix}_{key}"] = error["msg"]

    return mapped
