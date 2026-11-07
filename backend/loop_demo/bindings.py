"""A simple JSON path resolver for the independent demonstration."""
from copy import deepcopy
from typing import Any, Mapping
from .errors import BindingResolutionError


def resolve(root: Mapping[str, Any], path: str) -> Any:
    if not isinstance(path, str) or not path or path.startswith("."):
        raise BindingResolutionError(f"Invalid path: {path!r}")
    value: Any = root
    for segment in path.split("."):
        if isinstance(value, Mapping):
            if segment not in value:
                raise BindingResolutionError(f"Missing key {segment!r} in {path!r}")
            value = value[segment]
        elif isinstance(value, (list, tuple)) and segment.isdigit():
            index = int(segment)
            if index >= len(value):
                raise BindingResolutionError(f"Index {index} out of range for {path!r}")
            value = value[index]
        else:
            raise BindingResolutionError(f"Cannot resolve {segment!r} in {path!r}")
    return deepcopy(value)


def project(root: Mapping[str, Any], bindings: Mapping[str, str]) -> dict[str, Any]:
    return {alias: resolve(root, path) for alias, path in bindings.items()}
