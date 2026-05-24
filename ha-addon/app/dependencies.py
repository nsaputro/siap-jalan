from fastapi import Request


def get_ha_user(request: Request) -> str:
    return request.headers.get("X-Ingress-User", "default")
