# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, math, logging, secrets, mimetypes
from urllib.parse import quote
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

@routes.get(r"/watch/{path:.+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:/\S+)?", path).group(1))
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

@routes.get(r"/download/{path:.+}", allow_head=True)
async def download_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"(\d+)", path)
        if not match:
            raise web.HTTPNotFound(text="Invalid download link")
        id = int(match.group(1))
        secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash, force_download=True)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        raise web.HTTPBadRequest(text="Download connection interrupted")
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))


@routes.get(r"/stream/{path:.+}", allow_head=True)
async def inline_stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"(\d+)", path)
        if not match:
            raise web.HTTPNotFound(text="Invalid stream link")
        id = int(match.group(1))
        secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash, force_download=False)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        raise web.HTTPBadRequest(text="Stream connection interrupted")
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

@routes.get(r"/{path:.+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        # Plain file URLs are download links; browser playback is handled by /watch/.
        return await media_streamer(request, id, secure_hash, force_download=True)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError) as e:
    logging.warning("Client connection interrupted: %s", e)
    raise web.HTTPBadRequest(text="Connection interrupted")
    except Exception as e:
        logging.critical(e.with_traceback(None))l
        
        raise web.HTTPInternalServerError(text=str(e))

class_cache = {}

async def media_streamer(request: web.Request, id: int, secure_hash: str, force_download: bool = False):
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(id)
    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size
    range_header = request.headers.get("Range")
    status = 200

    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match or (not match.group(1) and not match.group(2)):
            return web.Response(
                status=416,
                text="416: Range not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"},
            )

        start_text, end_text = match.groups()
        if start_text:
            from_bytes = int(start_text)
            until_bytes = int(end_text) if end_text else file_size - 1
        else:
            suffix_length = int(end_text)
            from_bytes = max(file_size - suffix_length, 0)
            until_bytes = file_size - 1

        if from_bytes >= file_size or until_bytes < from_bytes:
            return web.Response(
                status=416,
                text="416: Range not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"},
            )
        until_bytes = min(until_bytes, file_size - 1)
        status = 206
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    chunk_size = 1024 * 1024
    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1
    part_count = ((until_bytes - offset) // chunk_size) + 1

    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    file_name = file_id.file_name or f"{secrets.token_hex(2)}.unknown"
    mime_type = file_id.mime_type or mimetypes.guess_type(file_name)[0]
    mime_type = mime_type or "application/octet-stream"

    disposition = "attachment" if force_download or request.rel_url.query.get("download") == "1" else "inline"
    ascii_name = file_name.encode("ascii", "ignore").decode("ascii") or "download"
    ascii_name = ascii_name.replace('"', "'").replace("\\", "_")
    encoded_name = quote(file_name, safe="")

    headers = {
        "Content-Type": mime_type,
        "Content-Length": str(until_bytes - from_bytes + 1),
        "Content-Disposition": f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}",
        "Accept-Ranges": "bytes",
    }
    if status == 206:
        headers["Content-Range"] = f"bytes {from_bytes}-{until_bytes}/{file_size}"

    # StreamResponse is required here: web.Response cannot consume an async
    # iterator, so the old handler never delivered Telegram's media chunks.
    response = web.StreamResponse(status=status, headers=headers)
    await response.prepare(request)

    if request.method != "HEAD":
        async for chunk in body:
            await response.write(chunk)

    await response.write_eof()
    return response
