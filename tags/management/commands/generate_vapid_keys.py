from django.core.management.base import BaseCommand
from tags.push_notifications import generate_vapid_keys


class Command(BaseCommand):
    help = 'Generate VAPID keys for Web Push notifications'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Generating VAPID Keys for Push Notifications'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        try:
            public_key, private_key = generate_vapid_keys()

            self.stdout.write(self.style.SUCCESS('\n✅ VAPID Keys Generated Successfully!\n'))
            self.stdout.write(self.style.WARNING('Add these to your .env file:\n'))
            self.stdout.write(f'VAPID_PUBLIC_KEY={public_key}')
            self.stdout.write(f'VAPID_PRIVATE_KEY={private_key}')
            self.stdout.write(f'VAPID_ADMIN_EMAIL=mailto:admin@ghnoticeboard.com\n')

            self.stdout.write(self.style.WARNING('⚠️  Keep the private key secret and never commit it to git!\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating keys: {str(e)}'))
