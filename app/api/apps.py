from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    Configuration class for the 'api' Django application.

    This class defines the default settings
    for the 'api' application, including:
    - `default_auto_field`:
    Specifies the default auto-generated field type for models
    within the application.
    In this case, it uses `BigAutoField` to support larger
    integer values for primary keys.
    - `name`: The name of the application,
              which is used by Django to identify and load
              the application. Here, it is set to `'api'`.

    This configuration ensures proper
    initialization and behavior of the application within the Django project.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
