"""Cloudinary-backed media storage.

Uploads keep surviving restarts and redeploys on free hosts with ephemeral disks, and
images are served through Cloudinary's CDN in the best format the browser supports.
"""

import uuid
from pathlib import PurePosixPath

import cloudinary.uploader
from cloudinary import CloudinaryImage
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

DEFAULT_WIDTH = 1080


@deconstructible
class CloudinaryMediaStorage(Storage):
    def __init__(self, folder="petconnect"):
        self.folder = folder

    def _save(self, name, content):
        directory = PurePosixPath(name).parent
        prefix = self.folder if str(directory) == "." else f"{self.folder}/{directory}"
        if hasattr(content, "seek"):
            content.seek(0)
        result = cloudinary.uploader.upload(
            content,
            public_id=f"{prefix}/{uuid.uuid4().hex}",
            resource_type="image",
            overwrite=False,
        )
        return result["public_id"]

    def _open(self, name, mode="rb"):
        raise NotImplementedError("Cloudinary media is served by URL, not read back from disk.")

    def exists(self, name):
        return False

    def delete(self, name):
        if name:
            cloudinary.uploader.destroy(name, resource_type="image")

    def size(self, name):
        return 0

    def url(self, name):
        return self.resized_url(name, DEFAULT_WIDTH)

    def resized_url(self, name, width):
        return CloudinaryImage(name).build_url(
            secure=True,
            fetch_format="auto",
            quality="auto",
            width=width,
            crop="limit",
        )
