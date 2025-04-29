from django.apps import AppConfig


class HealthboxConfig(AppConfig):
    """
    Configuration class for the 'healthbox' Django application.

    This class defines the default settings for the 'healthbox' application,
    including:
    - `default_auto_field`:
    Specifies the default auto-generated field type for models
    within the application.
    In this case, it uses `BigAutoField`
    to support larger integer values for primary keys.
    - `name`: The full Python path to the application,
              which is used by Django to identify
              and load the application. Here, it is set to `'app.healthbox'`.

    This configuration ensures proper initialization
    and behavior of the application within the Django project.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.healthbox'
