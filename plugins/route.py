# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, math, logging, secrets, mimetypes, time, asyncio
from info import *
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from TechVJ.bot import multi_clients, work_loads, TechVJBot
from TechVJ.server.exceptions import FIleNotFound, InvalidHash
from TechVJ import StartTime, __version__
from TechVJ.util.custom_dl import ByteStreamer
from TechVJ.util.time_format import get_readable_time
from TechVJ.util.render_template import render_page

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("BenFilterBot")

def parse_stream_path(request: web.Request):
    """Return (message_id, hash) or raise a clean 404 for unrelated paths."""
    path = request.match_info.get("path", "")
    match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
    if match:
        return int(match.group(2)), match.group(1)

    match = re.search(r"(\d+)(?:/|$)", path)
    if not match:
        raise web.HTTPNotFound(text="Invalid file link")
    return int(match.group(1)), request.rel_url.query.get("hash")


@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        id, secure_hash = parse_stream_path(request)
        return web.Response(
            text=await render_page(id, secure_hash),
            content_type="text/html",
        )
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (BadStatusLine, ConnectionResetError):
        logging.info("Client disconnected while loading player page")
        raise web.HTTPClientError(text="Client disconnected")
    except web.HTTPException:
        raise
    except Exception:
        logging.exception("Player page request failed")
        raise web.HTTPInternalServerError(text="Unable to load player page")


@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        id, secure_hash = parse_stream_path(request)
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (BadStatusLine, ConnectionResetError):
        logging.info("Client disconnected while handling stream request")
        raise web.HTTPClientError(text="Client disconnected")
    except web.HTTPException:
        raise
    except Exception:
        logging.exception("Media stream request failed")
        raise web.HTTPInternalServerError(text="Unable to stream media")


class_cache = {}


async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range")

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
    else:
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(id)
    if not secure_hash or file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size
    if not file_size:
        raise web.HTTPNotFound(text="Empty media file")

    # Parse a single HTTP byte range (including open-ended and suffix ranges).
    from_bytes, until_bytes = 0, file_size - 1
    is_partial = False
    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match or (not match.group(1) and not match.group(2)):
            raise web.HTTPRequestRangeNotSatisfiable(
                headers={"Content-Range": f"bytes */{file_size}"}
            )
        first, last = match.groups()
        if not first:
            suffix_length = int(last)
            if suffix_length <= 0:
                raise web.HTTPRequestRangeNotSatisfiable(
                    headers={"Content-Range": f"bytes */{file_size}"}
                )
            from_bytes = max(0, file_size - suffix_length)
        else:
            from_bytes = int(first)
            until_bytes = int(last) if last else file_size - 1
        if from_bytes >= file_size or until_bytes < from_bytes:
            raise web.HTTPRequestRangeNotSatisfiable(
                headers={"Content-Range": f"bytes */{file_size}"}
            )
        until_bytes = min(until_bytes, file_size - 1)
        is_partial = True

    chunk_size = 1024 * 1024
    offset = (from_bytes // chunk_size) * chunk_size
    first_part_cut = from_bytes - offset
    last_part_cut = (until_bytes % chunk_size) + 1
    req_length = until_bytes - from_bytes + 1
    # Inclusive chunk count: avoids a zero/short stream at exact chunk boundaries.
    part_count = ((until_bytes // chunk_size) - (offset // chunk_size)) + 1

    guessed_mime = mimetypes.guess_type(file_id.file_name or "")[0]
    mime_type = file_id.mime_type or ""
    if not mime_type or mime_type == "application/octet-stream":
        mime_type = guessed_mime or mime_type or "application/octet-stream"
    file_name = file_id.file_name or f"{secrets.token_hex(4)}.bin"
    safe_name = file_name.replace('"', "'").replace("\", "_")
    disposition = "inline" if mime_type.startswith(("video/", "audio/")) else "attachment"

    headers = {
        "Content-Type": mime_type,
        "Content-Length": str(req_length),
        "Content-Disposition": f'{disposition}; filename="{safe_name}"',
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if is_partial:
        headers["Content-Range"] = f"bytes {from_bytes}-{until_bytes}/{file_size}"

    response = web.StreamResponse(
        status=206 if is_partial else 200,
        headers=headers,
    )
    await response.prepare(request)

    # HEAD requests need headers only; GET streams Telegram chunks progressively.
    if request.method == "HEAD":
        return response

    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )
    try:
        async for chunk in body:
            if chunk:
                await response.write(chunk)
        await response.write_eof()
    except (ConnectionResetError, asyncio.CancelledError):
        logging.info("Client disconnected while streaming message %s", id)
        raise

    return response
