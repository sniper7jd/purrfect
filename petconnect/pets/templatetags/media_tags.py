from django import template

register = template.Library()


@register.filter
def resized(fieldfile, width):
    """URL for an image scaled to `width` px when the storage supports it (Cloudinary)."""
    if not fieldfile:
        return ""
    storage = fieldfile.storage
    if hasattr(storage, "resized_url"):
        return storage.resized_url(fieldfile.name, int(width))
    return fieldfile.url
