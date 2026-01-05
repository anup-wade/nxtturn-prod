# C:\Users\Vinay\Project\Loopline\community\management\commands\fix_group_memberships.py

from django.core.management.base import BaseCommand
from community.models import Group

class Command(BaseCommand):
    help = 'Ensures that the creator of every group is also a member of that group.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting to check group memberships..."))
        
        fixed_groups_count = 0
        groups_to_check = Group.objects.select_related('creator').all()

        for group in groups_to_check:
            # Check if the creator is already in the members list
            if not group.members.filter(id=group.creator.id).exists():
                self.stdout.write(self.style.WARNING(
                    f"Fixing group '{group.name}' (ID: {group.id}): Creator '{group.creator.username}' was not a member."
                ))
                # If not, add them
                group.members.add(group.creator)
                fixed_groups_count += 1
            else:
                self.stdout.write(
                    f"Checked group '{group.name}' (ID: {group.id}): OK."
                )

        if fixed_groups_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"\nFinished. Successfully fixed {fixed_groups_count} group(s)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\nFinished. All group memberships are correct. No changes needed."
            ))