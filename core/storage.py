"""Custom Cloudinary storage that generates correct URLs."""
import os

import cloudinary
import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage


class FixedMediaCloudinaryStorage(MediaCloudinaryStorage):
    """MediaCloudinaryStorage with fixed URL generation and proper resource types."""

    # File extensions that should use 'raw' resource type
    RAW_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv', '.zip'}
    # File extensions that should use 'video' resource type
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm', '.mkv'}

    def _get_resource_type(self, name):
        """Determine resource type based on file extension."""
        ext = os.path.splitext(name)[1].lower()
        if ext in self.RAW_EXTENSIONS:
            return 'raw'
        elif ext in self.VIDEO_EXTENSIONS:
            return 'video'
        return 'image'

    def _upload(self, name, content):
        """Upload with correct resource type based on file extension."""
        resource_type = self._get_resource_type(name)
        options = {
            'use_filename': True,
            'resource_type': resource_type,
            'tags': self.TAG,
        }
        folder = os.path.dirname(name)
        if folder:
            options['folder'] = folder
        return cloudinary.uploader.upload(content, **options)

    def _get_url(self, name):
        name = self._prepend_prefix(name)
        resource_type = self._get_resource_type(name)
        # Build URL without version to avoid 401 errors
        cloud_name = cloudinary.config().cloud_name
        return f"https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{name}"
