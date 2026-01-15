# C:\Users\Vinay\Project\Loopline\community\management\commands\clear_seeded_data.py
# FINAL VERSION - Deletes users from DB based on a file, then deletes the file.

import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Safely deletes users from the DB and removes their credential file."

    def add_arguments(self, parser):
        # The --file argument is required. The script will not run without it.
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="The credential file to process for cleanup (e.g., seeded_users.txt).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options["file"]
        file_path = os.path.join(settings.BASE_DIR, filename)

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(
                    f"Error: The specified file was not found: {file_path}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"--- Starting Safe Cleanup based on {filename} ---")
        )

        usernames_to_delete = []
        try:
            with open(file_path, "r") as f:
                for line in f:
                    match = re.search(r"^Username:\s*(\S+)", line)
                    if match:
                        usernames_to_delete.append(match.group(1))
        except IOError as e:
            self.stdout.write(self.style.ERROR(f"Error reading file: {e}"))
            return

        if not usernames_to_delete:
            self.stdout.write(
                self.style.WARNING(
                    "No usernames found in the specified file. Nothing to delete."
                )
            )
            return

        self.stdout.write(
            f"Found {len(usernames_to_delete)} usernames. Proceeding with DB deletion..."
        )

        # This simple query is all that's needed.
        # The database's 'on_delete=CASCADE' policy handles deleting all related content.
        users_to_delete = User.objects.filter(username__in=usernames_to_delete)

        deleted_count, _ = users_to_delete.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f" > Deleted {deleted_count} user accounts and all their associated data."
            )
        )

        # --- DELETE THE CREDENTIAL FILE ---
        self.stdout.write(f"Attempting to clean up the credential file...")
        try:
            os.remove(file_path)
            self.stdout.write(
                self.style.SUCCESS(
                    f" > Successfully deleted credential file: {filename}"
                )
            )
        except OSError as e:
            self.stdout.write(
                self.style.WARNING(f" > Could not delete the credential file: {e}")
            )
            self.stdout.write(
                self.style.WARNING(f"   Please remove it manually: {file_path}")
            )

        self.stdout.write(self.style.SUCCESS("--- SAFE DATA CLEANUP COMPLETE ---"))
