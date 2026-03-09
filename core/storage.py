from cloudinary_storage.storage import MediaCloudinaryStorage

class CustomCloudinaryStorage(MediaCloudinaryStorage):
    """
    Cloudinary storage or original folder structure will maintain
    Example: media/hero/profile_me.jpg → Cloudinary-তে uploads/hero/profile_me.jpg
    """
    def get_available_name(self, name, max_length=None):
        # keep original folder structure
        return name