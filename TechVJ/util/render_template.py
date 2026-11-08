import jinja2
from info import *
from TechVJ.bot import TechVJBot
from TechVJ.util.human_readable import humanbytes
from TechVJ.util.file_properties import get_file_ids
from TechVJ.server.exceptions import InvalidHash
import urllib.parse
import logging
import mimetypes


async def render_page(id, secure_hash, src=None):
    file_data = await get_file_ids(TechVJBot, int(LOG_CHANNEL), int(id))
    if not file_data:
        raise InvalidHash
    if not secure_hash or file_data.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with - ID {id}")
        raise InvalidHash

    file_name = file_data.file_name or f"media_{id}"
    mime_type = (
        file_data.mime_type
        or mimetypes.guess_type(file_name)[0]
        or "application/octet-stream"
    )
    if mime_type == "application/octet-stream":
        logging.warning("Unknown media MIME type for message %s (%s)", id, file_name)

    src = urllib.parse.urljoin(
        URL,
        f"{id}/{urllib.parse.quote(file_name)}?hash={secure_hash}",
    )

    tag = mime_type.split("/")[0].strip()
    file_size = humanbytes(file_data.file_size)
    if tag in ["video", "audio"]:
        template_file = "TechVJ/template/req.html"
    else:
        template_file = "TechVJ/template/dl.html"

    with open(template_file, encoding="utf-8") as f:
        template = jinja2.Template(f.read())

    display_name = file_name.replace("_", " ")

    return template.render(
        file_name=display_name,
        file_url=src,
        file_size=file_size,
        file_unique_id=file_data.unique_id,
        mime_type=mime_type,
    )
