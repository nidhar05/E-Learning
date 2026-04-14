import mimetypes
import os
import re
from datetime import datetime

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.utils.http import http_date

RANGE_PATTERN = re.compile(r"bytes=(\d+)-(\d*)")


def serve_media(request, path):
    file_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, path))
    if not file_path.startswith(str(settings.MEDIA_ROOT)) or not os.path.exists(file_path):
        raise Http404("Media file not found")

    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"

    range_header = request.headers.get("Range")
    if range_header:
        match = RANGE_PATTERN.match(range_header)
        if match:
            start = int(match.group(1))
            end_part = match.group(2)
            end = int(end_part) if end_part else file_size - 1
            if end >= file_size:
                end = file_size - 1
            if start > end:
                return HttpResponse(status=416)

            length = end - start + 1
            file_obj = open(file_path, "rb")
            file_obj.seek(start)
            response = FileResponse(file_obj, status=206, content_type=content_type)
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Accept-Ranges"] = "bytes"
            response["Content-Length"] = str(length)
            response["Last-Modified"] = http_date(os.path.getmtime(file_path))
            return response

    file_obj = open(file_path, "rb")
    response = FileResponse(file_obj, content_type=content_type)
    response["Content-Length"] = str(file_size)
    response["Accept-Ranges"] = "bytes"
    response["Last-Modified"] = http_date(os.path.getmtime(file_path))
    return response
