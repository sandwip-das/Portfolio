from django.core.management.base import BaseCommand
from core.sqlite_cloudinary import upload_db_to_cloudinary, download_db_from_cloudinary


class Command(BaseCommand):
    help = "Synchronizes SQLite database (db.sqlite3) with Cloudinary storage."

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['push', 'pull'],
            default='push',
            help="Action to perform: 'push' to upload local DB to Cloudinary, 'pull' to download from Cloudinary."
        )

    def handle(self, *args, **options):
        action = options['action']
        if action == 'push':
            self.stdout.write("Uploading SQLite DB to Cloudinary...")
            success = upload_db_to_cloudinary()
            if success:
                self.stdout.write(self.style.SUCCESS("Successfully uploaded SQLite DB to Cloudinary."))
            else:
                self.stdout.write(self.style.ERROR("Failed to upload SQLite DB to Cloudinary."))
        elif action == 'pull':
            self.stdout.write("Downloading SQLite DB from Cloudinary...")
            success = download_db_from_cloudinary()
            if success:
                self.stdout.write(self.style.SUCCESS("Successfully downloaded SQLite DB from Cloudinary."))
            else:
                self.stdout.write(self.style.WARNING("Could not download SQLite DB from Cloudinary."))
