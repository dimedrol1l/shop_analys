# apps.py
from django.apps import AppConfig

class Cy19346ProjectConfig(AppConfig):
    name = 'cy19346_project'

    def ready(self):
        import cy19346_project.signals
