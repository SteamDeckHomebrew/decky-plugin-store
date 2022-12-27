from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic.utils import ROOT_KEY

if TYPE_CHECKING:
    from typing import Any, Union

    from pydantic.typing import DictStrAny


class PluginVersion(BaseModel):
    name: str
    hash: str


class PluginWithoutImageAndVisibility(BaseModel):
    id: int
    name: str
    author: str
    description: str
    tags: list[str]
    versions: list[PluginVersion]


class PluginWithoutImage(PluginWithoutImageAndVisibility):
    visible: bool


class PluginWithoutVisibility(PluginWithoutImageAndVisibility):
    image_url: str


class Plugin(PluginWithoutVisibility):
    visible: bool


class BasePluginRequest(PluginWithoutImage):
    pass


class PluginTagResponse(BaseModel):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

    __root__: str = Field(alias="tag")

    @classmethod
    def _enforce_dict_if_root(cls, obj: "Any") -> "Any":
        if cls.__custom_root_type__ and cls.__fields__[ROOT_KEY].alt_alias:
            return dict(cls._decompose_class(obj))

        return super()._enforce_dict_if_root(obj)

    def dict(self, **kwargs) -> "Union[DictStrAny, str]":
        if self.__custom_root_type__:
            data = super().dict(**{**kwargs, "by_alias": False})
            return data[ROOT_KEY]
        return super().dict(**kwargs)


class PluginVersionResponse(PluginVersion):
    class Config:
        orm_mode = True


class BasePluginResponseWithoutVisibility(PluginWithoutVisibility):
    class Config:
        orm_mode = True

    tags: list[PluginTagResponse]
    versions: list[PluginVersionResponse]

    @classmethod
    def from_orm(cls, *args, **kwargs):
        return super().from_orm(*args, **kwargs)


class BasePluginResponse(Plugin):
    class Config:
        orm_mode = True

    tags: list[PluginTagResponse]
    versions: list[PluginVersionResponse]
