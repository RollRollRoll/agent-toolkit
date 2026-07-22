"""变量递归解析与目标值替换。"""

from __future__ import annotations

import os
from typing import Any, Mapping

from .errors import ConfigError


def _placeholders(text: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    stack: list[int] = []
    index = 0
    while index < len(text):
        if text[index : index + 2] == "${":
            stack.append(index)
            index += 2
            continue
        if text[index] == "}" and stack:
            start = stack.pop()
            found.append((start, index + 1, text[start + 2 : index]))
        index += 1
    if stack:
        raise ConfigError("CONFIG_SCHEMA_INVALID", f"变量表达式缺少右花括号：{text!r}")
    return found


def resolve_variables(
    definitions: Mapping[str, Any],
    context: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = os.environ if environ is None else environ
    sources: dict[str, Any] = {key: value for key, value in context.items() if key != "tags" and value is not None}
    sources.update(definitions)
    resolved: dict[str, str] = {}

    def resolve_name(name: str, stack: tuple[str, ...]) -> str:
        if name in resolved:
            return resolved[name]
        if name in stack:
            cycle = " -> ".join((*stack, name))
            raise ConfigError("VARIABLE_CYCLE", f"检测到变量循环引用：{cycle}", location=name)
        if name not in sources:
            raise ConfigError("VARIABLE_NOT_FOUND", f"变量未定义：${{{name}}}", location=name)
        value = sources[name]
        if isinstance(value, (dict, list)):
            raise ConfigError("CONFIG_SCHEMA_INVALID", "变量值必须是标量。", location=name)
        result = substitute(str(value), (*stack, name))
        resolved[name] = result
        return result

    def resolve_token(token: str, stack: tuple[str, ...]) -> str:
        if token.startswith("env:"):
            expression = token[4:]
            name, separator, default = expression.partition(":-")
            if env.get(name) is not None:
                return env[name]
            if separator:
                return substitute(default, stack)
            raise ConfigError("VARIABLE_NOT_FOUND", f"环境变量未定义：${{env:{name}}}", location=f"env:{name}")
        return resolve_name(token, stack)

    def substitute(text: str, stack: tuple[str, ...] = ()) -> str:
        # 从右向左替换，避免前一个替换改变后续索引。
        while True:
            tokens = _placeholders(text)
            if not tokens:
                return text
            innermost = [item for item in tokens if "${" not in item[2]]
            if not innermost:
                raise ConfigError("CONFIG_SCHEMA_INVALID", f"无法解析变量表达式：{text!r}")
            for start, end, token in reversed(innermost):
                text = text[:start] + resolve_token(token, stack) + text[end:]

    for variable_name in sources:
        resolve_name(variable_name, ())
    return resolved


def substitute_tree(
    value: Any,
    variables: Mapping[str, str],
    *,
    location: str = "",
    environ: Mapping[str, str] | None = None,
) -> Any:
    env = os.environ if environ is None else environ
    if isinstance(value, dict):
        return {
            key: substitute_tree(
                child,
                variables,
                location=f"{location}.{key}" if location else str(key),
                environ=env,
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [
            substitute_tree(child, variables, location=f"{location}[{index}]", environ=env)
            for index, child in enumerate(value)
        ]
    if not isinstance(value, str):
        return value

    text = value
    while True:
        tokens = _placeholders(text)
        if not tokens:
            return text
        innermost = [item for item in tokens if "${" not in item[2]]
        for start, end, token in reversed(innermost):
            if token.startswith("env:"):
                expression = token[4:]
                name, separator, default = expression.partition(":-")
                if env.get(name) is not None:
                    replacement = env[name]
                elif separator:
                    replacement = default
                else:
                    raise ConfigError("VARIABLE_NOT_FOUND", f"环境变量未定义：${{env:{name}}}", location=location)
            elif token in variables:
                replacement = variables[token]
            else:
                raise ConfigError("VARIABLE_NOT_FOUND", f"变量未定义：${{{token}}}", location=location)
            text = text[:start] + replacement + text[end:]
