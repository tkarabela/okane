from typing import Any
from lxml.etree import _Element
import datetime
import warnings


def get_text_or_none(e: _Element | None, path: str | None = None, strip: bool = True) -> str | None:
    if e is None:
        return None
    else:
        if path is not None:
            e = e.find(path)

        if e is None:
            return None
        else:
            text = e.text
            if strip and text is not None:
                text = text.strip()
            return text


def get_text(e: _Element | None, path: str | None = None, strip: bool = True) -> str:
    text = get_text_or_none(e, path, strip)
    if text is None:
        raise ValueError("Missing mandatory element")
    return text


def get_element(root: _Element, path: str) -> _Element:
    e = root.find(path)
    if e is None:
        raise ValueError(f"Missing mandatory element ({path})")
    return e


def get_attribute(e: _Element, attr: str) -> str:
    value = e.attrib[attr]
    return str(value)


def parse_date_isoformat(s: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        warnings.warn(f"Invalid isoformat string: {s!r}", RuntimeWarning)
        return datetime.date.fromisoformat(s[:10])


def flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    output = {}
    for k, v in d.items():
        if isinstance(v, dict):
            output.update(flatten_dict(v, prefix=f"{prefix}{k}."))
        else:
            output[f"{prefix}{k}"] = v
    return output
