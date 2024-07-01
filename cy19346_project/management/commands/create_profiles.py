from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cy19346_project.models import Profile

class Command(BaseCommand):
    help = 'Create profiles for users who do not have one'

    def handle(self, *args, **kwargs):
        users_without_profile = User.objects.filter(profile__isnull=True)
        for user in users_without_profile:
            Profile.objects.create(user=user)
        self.stdout.write(self.style.SUCCESS('Successfully created profiles for all users without one'))
