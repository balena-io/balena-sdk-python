from .balena_auth import request
from .settings import settings
from .exceptions import BuilderRequestError


def build_from_url(owner: str, app_name: str, url: str, flatten_tarball: bool) -> int:
    res = request(
        method="post",
        path=f"/v3/buildFromUrl?headless=true&owner={owner}&app={app_name}",
        endpoint=settings.get("builder_url"),
        body={
            "url": url,
            "shouldFlatten": flatten_tarball
        }
    )
    if not res.get("started"):
        raise BuilderRequestError(res.get("message"))

    return res["releaseId"]
