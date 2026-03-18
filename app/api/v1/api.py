import os
import importlib
from fastapi import APIRouter

api_router = APIRouter()

BASE_DIR = os.path.dirname(__file__)
ENDPOINTS_DIR = os.path.join(BASE_DIR, "endpoints")

for file in os.listdir(ENDPOINTS_DIR):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]

        module = importlib.import_module(
            f"app.api.v1.endpoints.{module_name}"
        )

        router = getattr(module, "router", None)

        if router:
            api_router.include_router(
                router,
                prefix=f"/{module_name}",
                tags=[module_name.capitalize()],
            )