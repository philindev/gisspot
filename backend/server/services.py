from datetime import datetime
from typing import Optional, List, Dict

from .pd_model import *
from .settings import REQUEST_TYPES, DATABASE_URL

from ..database.core import gis_stac
from ..queue.services import add_task

__all__ = ["main_processing"]


def main_processing(data: Optional[StandardModel]) \
        -> Optional[StandardModel]:
    response = StandardModel(type=data.type, data={})
    try:
        assert data.type in REQUEST_TYPES

        if data.type == "fetchPreview":
            response.data = preview_processing(PreviewData(**data.data))

    except AttributeError:
        response.data["status"] = False
        response.data["message"] = "Type is not corrected"
    else:
        if response.data == {}:
            response.data["status"] = True
            response.data["message"] = "Processing"
    return response


def get_items(time_interval: List[datetime], bbox: List[float]) -> List[dict]:
    # response = get(DATABASE_URL + "get_preview") # TODO: Запрос к базе данных через url
    items = gis_stac.filter(time_intervals=[time_interval], bboxes=[bbox])
    items = sorted(map(lambda item: item.to_dict(), items),
                   key=lambda item: item["datetime"])
    return list(items)


def preview_interval(timestamp: int) -> List[datetime]:
    return [datetime.fromtimestamp(timestamp),
            datetime.fromtimestamp(timestamp + 24 * 60 * 60)]


def preview_processing(data: PreviewData) -> Dict[str, List[PreviewData]]:
    items = get_items(preview_interval(data.datetime),
                      [data.bbox[0].lat, data.bbox[0].lon,
                       data.bbox[1].lat, data.bbox[1].lon])
    res = []
    for item in items:
        for asset in item["assets"]:
            if asset["type"] == "img":
                res.append(PreviewData(img=asset["href"], datetime=item["properties"]["datetime"], bbox=item["bbox"]))
                break

    return {"imgs": res}


def get_item_url(iid: Optional[str]) -> str:
    item = gis_stac.root_catalog.get_child(iid, recursive=True)
    return item.href


def vector_processing(data: VectorsRequest) -> None:
    files = (get_item_url(data.ids[0]), get_item_url(data.ids[1]))
    params = [files[0], files[1], data.points, data.window_size, data.vicinity_size]
    add_to_queue(ws_id=1, task_type="high", *params)


def add_to_queue(ws_id: Optional[int] = None,
                 task_type: Optional[str] = "high",
                 *params, **kwargs) -> None:
    request_data = {"task_type": task_type,
                    "params": params,
                    "kwargs": kwargs}
    if ws_id is not None:
        request_data["ws_id"] = ws_id

    # Либо вызов методы (модульная архитектурка)
    # Либо запрос к серверу очереди (микросервесы)
