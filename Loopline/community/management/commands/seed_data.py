# C:\Users\Vinay\Project\Loopline\community\management\commands\seed_data.py
# FINAL "WORLD BUILDER" VERSION (With Interactive Domain & Dynamic Credential Files)

import random
import os
import requests
from io import BytesIO

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from community.models import Follow, StatusPost, Group, UserProfile, PostMedia
from faker import Faker
from django.core.files import File
from django.core.files.base import ContentFile

User = get_user_model()


class Command(BaseCommand):
    help = "Builds a rich world of users with a custom domain, and saves credentials to a domain-specific file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=None,
            help="Number of users to create. If not provided, script will ask.",
        )
        parser.add_argument(
            "--posts", type=int, default=100, help="Total number of posts to create."
        )
        parser.add_argument(
            "--groups", type=int, default=10, help="Number of groups to create."
        )
        parser.add_argument(
            "--max-follows", type=int, default=20, help="Max follows per user."
        )
        parser.add_argument(
            "--max-groups-joined",
            type=int,
            default=5,
            help="Max groups a user will join.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        num_users = options["users"]

        default_domain = "seededdata.com"
        prompt = f" > Enter the email domain to use (press Enter for default '{default_domain}'): "
        domain_input = input(self.style.SUCCESS(prompt)).strip()
        domain = domain_input if domain_input else default_domain
        self.stdout.write(self.style.NOTICE(f"Using email domain: @{domain}"))

        if domain == default_domain:
            output_filename = "seeded_users.txt"
        else:
            safe_domain_name = domain.replace(".", "_")
            output_filename = f"seeded_users_{safe_domain_name}.txt"

        if num_users is None:
            self.stdout.write(
                self.style.NOTICE("Number of users not specified via --users flag.")
            )
            while True:
                try:
                    response = input(
                        self.style.SUCCESS(
                            " > How many users would you like to create? "
                        )
                    )
                    num_users = int(response)
                    if num_users > 0:
                        break
                    else:
                        self.stdout.write(
                            self.style.ERROR("   Please enter a number greater than 0.")
                        )
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR(
                            "   Invalid input. Please enter a whole number."
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n--- Starting Rich World Builder: Creating {num_users} Users ---"
            )
        )
        faker = Faker()
        created_users_credentials = []
        users = []

        self.stdout.write(f"Creating {num_users} users with profiles...")
        for i in range(num_users):
            first_name = faker.first_name()
            last_name = faker.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(100, 999)}_{i}"
            email = f"{username}@{domain}"
            password = "password123"
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                EmailAddress.objects.update_or_create(
                    user=user,
                    email=user.email,
                    defaults={"primary": True, "verified": True},
                )
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.bio = faker.sentence(nb_words=15)
                try:
                    avatar_url = f"https://robohash.org/{username}.png?set=set4"
                    response = requests.get(avatar_url, stream=True, timeout=10)
                    if response.status_code == 200:
                        image_content = ContentFile(response.content)
                        profile.picture.save(
                            f"{username}_avatar.png", image_content, save=True
                        )
                except requests.exceptions.RequestException:
                    pass
                users.append(user)
                created_users_credentials.append(
                    {"username": username, "email": email, "password": password}
                )
            except IntegrityError:
                continue
        self.stdout.write(
            self.style.SUCCESS(f" > Created {len(users)} users and profiles.")
        )

        self.stdout.write("Saving user credentials to file...")
        output_file_path = os.path.join(settings.BASE_DIR, output_filename)
        try:
            with open(output_file_path, "w") as f:
                f.write(f"Seeded User Credentials for nxtturn (domain: @{domain})\n")
                f.write("==================================================\n\n")
                for creds in created_users_credentials:
                    f.write(f"Username: {creds['username']}\n")
                    f.write(f"Email:    {creds['email']}\n")
                    f.write(f"Password: {creds['password']}\n")
                    f.write("---\n")
            self.stdout.write(
                self.style.SUCCESS(
                    f" > All {len(created_users_credentials)} user credentials saved to {output_file_path}"
                )
            )
        except IOError as e:
            self.stdout.write(
                self.style.ERROR(f" > FAILED to write credentials file: {e}")
            )

        num_groups = options["groups"]
        max_groups_joined = options["max_groups_joined"]
        max_follows = options["max_follows"]
        num_posts = options["posts"]
        self.stdout.write(f"Creating {num_groups} groups...")
        groups = []
        if users:
            for i in range(num_groups):
                group_name = faker.company() + " Hub"
                creator = random.choice(users)
                group = Group.objects.create(
                    name=group_name,
                    creator=creator,
                    description=faker.bs(),
                    privacy_level="public" if random.random() < 0.7 else "private",
                )
                group.members.add(creator)
                groups.append(group)
            self.stdout.write(self.style.SUCCESS(f" > Created {len(groups)} groups."))
            self.stdout.write("Populating groups with members...")
            for user in users:
                num_groups_to_join = random.randint(
                    1, min(max_groups_joined, len(groups))
                )
                if num_groups_to_join > 0:
                    groups_to_join = random.sample(groups, num_groups_to_join)
                    for group in groups_to_join:
                        group.members.add(user)
            self.stdout.write(self.style.SUCCESS(" > Group population complete."))
            self.stdout.write("Creating the social graph...")
            for user in users:
                num_to_follow = random.randint(1, min(max_follows, len(users) - 1))
                potential_follows = [u for u in users if u != user]
                if potential_follows and num_to_follow > 0:
                    users_to_follow = random.sample(potential_follows, num_to_follow)
                    for user_to_follow in users_to_follow:
                        Follow.objects.get_or_create(
                            follower=user, following=user_to_follow
                        )
            self.stdout.write(self.style.SUCCESS(" > Social graph created."))
            self.stdout.write(f"Creating {num_posts} initial posts...")
            seed_media_dir = os.path.join(settings.BASE_DIR.parent, "seed_media")
            images_dir = os.path.join(seed_media_dir, "images")
            videos_dir = os.path.join(seed_media_dir, "videos")
            image_files = (
                [
                    f
                    for f in os.listdir(images_dir)
                    if f.endswith(("jpg", "jpeg", "png"))
                ]
                if os.path.exists(images_dir)
                else []
            )
            video_files = (
                [f for f in os.listdir(videos_dir) if f.endswith(("mp4", "mov", "avi"))]
                if os.path.exists(videos_dir)
                else []
            )
            for i in range(num_posts):
                author = random.choice(users)
                content = faker.paragraph(nb_sentences=random.randint(2, 5))
                post = StatusPost.objects.create(author=author, content=content)
                roll = random.random()
                if image_files and roll < 0.25:
                    image_to_add = random.choice(image_files)
                    image_path = os.path.join(images_dir, image_to_add)
                    with open(image_path, "rb") as f:
                        django_file = File(f, name=image_to_add)
                        PostMedia.objects.create(
                            post=post, media_type="image", file=django_file
                        )
                elif video_files and roll < 0.35:
                    video_to_add = random.choice(video_files)
                    video_path = os.path.join(videos_dir, video_to_add)
                    with open(video_path, "rb") as f:
                        django_file = File(f, name=video_to_add)
                        PostMedia.objects.create(
                            post=post, media_type="video", file=django_file
                        )
            self.stdout.write(self.style.SUCCESS(f" > Created {num_posts} posts."))
        self.stdout.write(
            self.style.SUCCESS('\n"Rich World Builder" seeding complete!')
        )
