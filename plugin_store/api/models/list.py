from api.models.base import Plugin, PluginWithoutVisibility


class ListPluginResponseWithoutVisibility(PluginWithoutVisibility):
    pass


class ListPluginResponse(Plugin):
    pass
