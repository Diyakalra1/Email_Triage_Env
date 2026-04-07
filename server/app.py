# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""FastAPI app wiring for inbox environment."""

from openenv.core.env_server.http_server import create_fastapi_app

try:
    from ..models import InboxAction, InboxObservation
    from .environment import InboxEnvironment
except Exception:
    from models import InboxAction, InboxObservation
    from server.environment import InboxEnvironment

app = create_fastapi_app(InboxEnvironment, InboxAction, InboxObservation)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
