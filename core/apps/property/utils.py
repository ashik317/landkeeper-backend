def certificate_file_upload_path(instance, filename):
    return f"compliance_certificates/{instance.property.id}/{filename}"


def tenant_avatar_upload_path(instance, filename):
    return f"tenant_avatars/{instance.id}/{filename}"
