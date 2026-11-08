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

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(text=await render_page(id, secure_hash), content_type='text/html')
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

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

    mime_type = file_id.mime_type or mimetypes.guess_type(file_id.file_name or "")[0]
    mime_type = mime_type or "application/octet-stream"
    file_name = file_id.file_name or f"{secrets.token_hex(4)}.bin"
    safe_name = file_name.replace('"', "'").replace("\\", "_")
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
