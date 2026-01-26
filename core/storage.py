"""Custom Cloudinary storage that generates correct URLs."""
import cloudinary
from cloudinary_storage.storage import MediaCloudinaryStorage


class FixedMediaCloudinaryStorage(MediaCloudinaryStorage):
    """MediaCloudinaryStorage with fixed URL generation (no version prefix)."""

    def _get_url(self, name):
        name = self._prepend_prefix(name)
        resource_type = self._get_resource_type(name)
        # Build URL without version to avoid 401 errors
        cloud_name = cloudinary.config().cloud_name
        return f"https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{name}"
