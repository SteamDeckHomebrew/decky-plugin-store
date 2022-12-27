from typing import Any, Callable, Optional

from fastapi import File, Form, UploadFile
from fastapi.params import Depends


def form_body(cls):
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(
                default=File(default=arg.default) if arg.annotation == UploadFile else Form(default=arg.default),
            )
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls


class FormBodyCls(Depends):
    def __init__(self, model: Any = None, *, use_cache: bool = True):
        super().__init__(form_body(model) if model else None, use_cache=use_cache)


def FormBody(model: Any = None, *, use_cache: bool = True) -> Any:
    return FormBodyCls(model=model, use_cache=use_cache)
