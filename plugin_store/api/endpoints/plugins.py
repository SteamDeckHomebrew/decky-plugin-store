from functools import reduce
from operator import add

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from cdn import upload_image, upload_version
from constants import SortDirection, SortType
from database.database import database, Database
from discord import post_announcement

from ..dependencies import auth_token, increment_limit_per_plugin, rate_limit
from ..models import delete as api_delete
from ..models import list as api_list
from ..models import submit as api_submit
from ..models import update as api_update
from ..utils import FormBody, getIpHash

router = APIRouter()


@router.get("/plugins", response_model=list[api_list.ListPluginResponse])
async def plugins_list(
    query: str = "",
    tags: list[str] = Query(default=[]),
    hidden: bool = False,
    sort_by: SortType | None = None,
    sort_direction: SortDirection = SortDirection.ASC,
    db: "Database" = Depends(database),
):
    tags = list(filter(None, reduce(add, (el.split(",") for el in tags), [])))
    plugins = await db.search(db.session, query, tags, hidden, sort_by, sort_direction)
    return plugins


@router.post("/plugins/{plugin_name}/versions/{version_name}/increment", responses={404: {}, 429: {}})
async def increment_plugin_install_count(
    request: Request,
    plugin_name: str,
    version_name: str,
    isUpdate: bool = True,
    db: "Database" = Depends(database),
):
    ip = getIpHash(request)
    if not rate_limit.test(increment_limit_per_plugin, plugin_name, ip):
        return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    success = await db.increment_installs(db.session, plugin_name, version_name, isUpdate)
    if success:
        rate_limit.hit(increment_limit_per_plugin, plugin_name, ip)
        return Response(status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/__submit",
    dependencies=[Depends(auth_token)],
    response_model=api_submit.SubmitProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_release(
    data: "api_submit.SubmitProductRequest" = FormBody(api_submit.SubmitProductRequest),
    db: "Database" = Depends(database),
):
    plugin = await db.get_plugin_by_name(db.session, data.name)

    if plugin and data.force:
        await db.delete_plugin(db.session, plugin.id)
        plugin = None

    image_path = await upload_image(data.name, data.image)

    if plugin is not None:
        if data.version_name in [i.name for i in plugin.versions]:
            raise HTTPException(status_code=400, detail="Version already exists")
        plugin = await db.update_artifact(
            db.session,
            plugin,
            author=data.author,
            description=data.description,
            image_path=image_path,
            tags=list(filter(None, reduce(add, (el.split(",") for el in data.tags), []))),
        )
    else:
        plugin = await db.insert_artifact(
            session=db.session,
            name=data.name,
            author=data.author,
            description=data.description,
            image_path=image_path,
            tags=list(filter(None, reduce(add, (el.split(",") for el in data.tags), []))),
        )

    version = await db.insert_version(db.session, plugin.id, name=data.version_name, **await upload_version(data.file))

    await db.session.refresh(plugin)
    await post_announcement(plugin, version)
    return plugin


@router.post("/__update", dependencies=[Depends(auth_token)], response_model=api_update.UpdatePluginResponse)
async def update_plugin(data: "api_update.UpdatePluginRequest", db: "Database" = Depends(database)):
    old_plugin = await db.get_plugin_by_id(db.session, data.id)
    version_dates = {version.name: version.created for version in old_plugin.versions}
    await db.delete_plugin(db.session, data.id)
    new_plugin = await db.insert_artifact(
        db.session,
        image_path=old_plugin._image_path,
        **data.dict(exclude={"versions"}),
    )

    for version in reversed(data.versions):
        await db.insert_version(
            db.session,
            artifact_id=new_plugin.id,
            created=version_dates.get(version.name),
            **version.dict(),
        )
    await db.session.refresh(new_plugin)
    return new_plugin


@router.post("/__delete", dependencies=[Depends(auth_token)], status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(data: "api_delete.DeletePluginRequest", db: "Database" = Depends(database)):
    await db.delete_plugin(db.session, data.id)
