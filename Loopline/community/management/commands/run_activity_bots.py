# C:\Users\Vinay\Project\Loopline\community\management\commands\run_activity_bots.py
# COMPLETE & FINAL "DIRECTOR'S MODE" VERSION (With File Operation Fix)

import random
import time
import sys
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from community.models import (
    StatusPost, Follow, Like, Comment, Poll, PollOption, Group, PollVote, PostMedia
)
from faker import Faker

User = get_user_model()

class Command(BaseCommand):
    help = 'Runs an intelligent, observable simulation of user activity, including media posts.'

    def add_arguments(self, parser):
        parser.add_argument('--duration', type=int, default=60, help='Duration in minutes for the simulation.')
        parser.add_argument('--min-delay', type=int, default=5, help='Min seconds between actions.')
        parser.add_argument('--max-delay', type=int, default=20, help='Max seconds between actions.')
        parser.add_argument('--firehose', action='store_true', help='Run without delays for stress testing.')

    def handle(self, *args, **options):
        duration_minutes = options['duration']
        min_delay, max_delay = options['min_delay'], options['max_delay']
        is_firehose_mode = options['firehose']
        end_time = time.time() + duration_minutes * 60
        faker = Faker()

        # --- 1. GATHER ACTORS AND MEDIA ASSETS ---
        seeded_users = list(User.objects.filter(email__endswith='@example.com'))
        if not seeded_users:
            self.stdout.write(self.style.ERROR('No seeded users found. Run `seed_data` first.'))
            return
            
        seed_media_dir = os.path.join(settings.BASE_DIR.parent, 'seed_media')
        images_dir = os.path.join(seed_media_dir, 'images')
        videos_dir = os.path.join(seed_media_dir, 'videos')
        image_files = [f for f in os.listdir(images_dir) if f.endswith(('jpg', 'jpeg', 'png'))] if os.path.exists(images_dir) else []
        video_files = [f for f in os.listdir(videos_dir) if f.endswith(('mp4', 'mov', 'avi'))] if os.path.exists(videos_dir) else []
        
        self.stdout.write(f'Found {len(seeded_users)} bots and {len(image_files)} images, {len(video_files)} videos for posting.')

        # --- 2. INTERACTIVE SETUP FOR "DIRECTOR'S MODE" ---
        self.stdout.write(self.style.SUCCESS('\n--- Activity Simulator: Director\'s Mode Setup ---'))
        num_masters_str = input(f" > How many Master Accounts to observe? (Enter a number, e.g., 3): ")
        try:
            num_masters = int(num_masters_str)
            if num_masters > len(seeded_users): num_masters = len(seeded_users)
        except ValueError:
            num_masters = 0
        
        master_accounts = []
        if num_masters > 0:
            master_accounts = random.sample(seeded_users, num_masters)
            self.stdout.write(self.style.SUCCESS('\n--- MASTER ACCOUNT LOGIN INFO ---'))
            for i, user in enumerate(master_accounts):
                self.stdout.write(f"  {i+1}. Username: {user.username} | Password: password123")
            self.stdout.write(self.style.SUCCESS('----------------------------------'))
            input("\nPress Enter after you have logged into the Master Accounts to begin the simulation...")
        
        # --- 3. START SIMULATION ---
        mode = "FIREHOSE" if is_firehose_mode else "REALISTIC PACE"
        self.stdout.write(self.style.SUCCESS(f'\n--- Starting Simulation in {mode} mode for {duration_minutes} mins ---'))
        
        action_count = 0
        while time.time() < end_time:
            try:
                bot_user, target_user = self.choose_actors(seeded_users, master_accounts)
                
                action = random.choice(['post', 'post', 'like', 'comment', 'vote']) # Double 'post' to make it more likely
                
                if action == 'post':
                    self.create_mixed_content_post(bot_user, faker, images_dir, image_files, videos_dir, video_files)
                elif action == 'like':
                    self.perform_social_like(bot_user, target_user)
                elif action == 'comment':
                    self.perform_social_comment(bot_user, target_user, faker)
                elif action == 'vote':
                    self.perform_poll_vote(bot_user)

                action_count += 1
                if not is_firehose_mode:
                    time.sleep(random.uniform(min_delay, max_delay))
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nSimulation stopped by user.'))
                sys.exit()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f'\n--- Simulation finished. Performed {action_count} actions. ---'))

    def choose_actors(self, all_users, master_accounts):
        if master_accounts and random.random() < 0.5:
            if random.random() < 0.5:
                actor = random.choice(master_accounts)
                target = random.choice([u for u in all_users if u not in master_accounts] or all_users)
            else:
                actor = random.choice([u for u in all_users if u not in master_accounts] or all_users)
                target = random.choice(master_accounts)
        else:
            actor, target = random.sample(all_users, 2)
        return actor, target

    def create_mixed_content_post(self, author, faker, images_dir, image_files, videos_dir, video_files):
        action_type = "post"
        with transaction.atomic():
            content = faker.paragraph(nb_sentences=random.randint(2, 4))
            post = StatusPost.objects.create(author=author, content=content)
            
            media_roll = random.random()
            if image_files and media_roll < 0.25: # 25% chance for an image
                action_type = "image post"
                image_to_add = random.choice(image_files)
                image_path = os.path.join(images_dir, image_to_add)
                with open(image_path, 'rb') as f:
                    PostMedia.objects.create(post=post, media_type='image', file=File(f, name=image_to_add))
            elif video_files and media_roll < 0.35: # 10% chance for a video
                action_type = "video post"
                video_to_add = random.choice(video_files)
                video_path = os.path.join(videos_dir, video_to_add)
                with open(video_path, 'rb') as f:
                    PostMedia.objects.create(post=post, media_type='video', file=File(f, name=video_to_add))
            else:
                roll = random.random()
                if roll < 0.2: # 20% chance of a poll on a non-media post
                    action_type = "poll post"
                    question = faker.sentence(nb_words=random.randint(5, 10)).replace('.', '?')
                    post.content = question
                    post.save()
                    poll = Poll.objects.create(post=post, question=question)
                    for _ in range(random.randint(2, 4)):
                        PollOption.objects.create(poll=poll, text=faker.word().capitalize())
                elif roll < 0.4: # 20% chance of a group post
                    joined_groups = list(author.joined_groups.all())
                    if joined_groups:
                        action_type = "group post"
                        group = random.choice(joined_groups)
                        post.group = group
                        post.save()
                    else: # Fallback if user is in no groups
                        action_type = "text post (fallback)"
                else: # Remaining chance for a simple text post
                    action_type = "text post"
        self.stdout.write(f"  > Bot '{author.username}' created a new {action_type}.")

    def perform_social_like(self, bot_user, target_user):
        post_to_like = StatusPost.objects.filter(author=target_user).order_by('?').first()
        if post_to_like:
            Like.objects.get_or_create(user=bot_user, content_type=ContentType.objects.get_for_model(post_to_like), object_id=post_to_like.id)
            self.stdout.write(f"  > '{bot_user.username}' liked a post by '{target_user.username}'.")

    def perform_social_comment(self, bot_user, target_user, faker):
        post_to_comment_on = StatusPost.objects.filter(author=target_user).order_by('?').first()
        if post_to_comment_on:
            content = faker.sentence(nb_words=random.randint(4, 12))
            Comment.objects.create(author=bot_user, content=content, content_type=ContentType.objects.get_for_model(post_to_comment_on), object_id=post_to_comment_on.id)
            self.stdout.write(f"  > '{bot_user.username}' commented on a post by '{target_user.username}'.")

    def perform_poll_vote(self, bot_user):
        voted_poll_ids = PollVote.objects.filter(user=bot_user).values_list('poll_id', flat=True)
        poll_to_vote_on = Poll.objects.exclude(id__in=voted_poll_ids).order_by('?').first()
        if poll_to_vote_on:
            option_to_choose = poll_to_vote_on.options.order_by('?').first()
            if option_to_choose:
                PollVote.objects.create(user=bot_user, poll=poll_to_vote_on, option=option_to_choose)
                self.stdout.write(f"  > '{bot_user.username}' voted on a poll.")