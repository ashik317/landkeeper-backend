from django.contrib.auth.base_user import BaseUserManager


class ApplicantManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = email.lower().strip()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
