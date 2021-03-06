from rq import Queue
from redis import from_url

import sys
sys.path.append("../../")
from backend.queue.settings import REDIS_URL

__all__ = ["queues"]

redis_conn = from_url(REDIS_URL)
queues = {"default": Queue("default", connection=redis_conn),
          "high": Queue("high", connection=redis_conn)}
tasks = {"default": "backend.worker.services.worker_processing",
         "send": "backend.worker.services.send_result",
         "high": "backend.worker.services.big_worker"}
