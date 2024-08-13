import inspect
from typing import Any

from fastapi import File, Form, Request, UploadFile
from fastapi.params import Depends
from pydantic import UUID1


def getIpHash(request: Request):
    ip = request.headers.get("cf-connecting-ip")
    if ip is None:
        ip = request.client.host  # type: ignore [union-attr]
    return hash(ip)


def form_body(cls):
    # noinspection PyProtectedMember
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(
                default=(File if arg.annotation == UploadFile else Form)(
                    **{} if arg.default is inspect._empty else {"default": arg.default},
                ),
            )
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls


class FormBodyCls(Depends):
    def __init__(self, model: Any = None, *, use_cache: bool = True):
        super().__init__(form_body(model) if model else None, use_cache=use_cache)


# noinspection PyPep8Naming
def FormBody(model: Any = None, *, use_cache: bool = True) -> Any:
    return FormBodyCls(model=model, use_cache=use_cache)


class UUID7(UUID1):
    _required_version = 7
