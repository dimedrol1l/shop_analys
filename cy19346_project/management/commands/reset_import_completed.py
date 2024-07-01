from django.core.management.base import BaseCommand
from cy19346_project.models import Profile

class Command(BaseCommand):
    help = 'Reset import_completed for all user profiles'

    def handle(self, *args, **kwargs):
        profiles = Profile.objects.all()
        for profile in profiles:
            profile.import_completed = False
            profile.save()
        self.stdout.write(self.style.SUCCESS('Successfully reset import_completed for all profiles'))
