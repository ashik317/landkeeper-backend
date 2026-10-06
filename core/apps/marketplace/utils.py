def marketplace_category_icon_upload_path(instance, filename):
    # Unused by models; kept because migration 0001_initial references it.
    return f"marketplace/categories/{instance.alias}/{filename}"


def marketplace_provider_logo_upload_path(instance, filename):
    return f"marketplace/providers/{instance.alias}/{filename}"
