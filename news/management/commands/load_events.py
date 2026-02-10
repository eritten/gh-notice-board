# events/management/commands/load_events.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import random

from events.models import Event, EventCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Load 5 mock events for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating mock events...')

        # Get or create organizer user
        organizer, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ghananotice.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            organizer.set_password('admin123')
            organizer.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))

        # Create event categories
        categories_data = [
            {'name': 'Technology', 'icon': 'laptop', 'color': '#3B82F6'},
            {'name': 'Business', 'icon': 'briefcase', 'color': '#10B981'},
            {'name': 'Education', 'icon': 'book', 'color': '#F59E0B'},
            {'name': 'Networking', 'icon': 'users', 'color': '#8B5CF6'},
            {'name': 'Cultural', 'icon': 'music', 'color': '#EC4899'},
        ]

        event_categories = []
        for cat_data in categories_data:
            category, created = EventCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_active': True,
                }
            )
            event_categories.append(category)
            if created:
                self.stdout.write(f'  Created event category: {category.name}')

        # Mock events data
        events_data = [
            {
                'title': 'Ghana Tech Summit 2026',
                'summary': 'Premier technology conference in West Africa, bringing together innovators, entrepreneurs, and tech leaders.',
                'description': '''
Join us for the premier technology conference in West Africa, bringing together innovators, entrepreneurs, and tech leaders from across Ghana and beyond.

The Ghana Tech Summit 2026 features keynote speeches from industry leaders, panel discussions on emerging technologies, startup pitch competitions, and networking opportunities with investors and fellow tech enthusiasts.

Topics include:
- Artificial Intelligence and Machine Learning
- Fintech Innovation in Africa
- Blockchain and Cryptocurrency
- Mobile App Development
- Cybersecurity Best Practices
- Digital Transformation Strategies

Don't miss this opportunity to connect with the future of technology in Ghana!
                '''.strip(),
                'event_type': 'hybrid',
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=32),
                'venue_name': 'Accra International Conference Centre',
                'venue_address': 'Independence Avenue, Accra, Greater Accra Region, Ghana',
                'virtual_meeting_url': 'https://zoom.us/j/ghana-tech-summit',
                'contact_email': 'info@ghanatechsummit.com',
                'category': event_categories[0],  # Technology
                'registration_required': True,
                'max_attendees': 500,
                'price': 150.00,
                'currency': 'GHS',
                'is_featured': True,
                'is_trending': True,
            },
            {
                'title': 'Startup Founders Networking Mixer',
                'summary': 'Exclusive networking event for startup founders, entrepreneurs, and investors in the Ghanaian ecosystem.',
                'description': '''
An exclusive networking event for startup founders, entrepreneurs, and investors in the Ghanaian ecosystem.

Connect with like-minded individuals, share experiences, find potential co-founders, and meet investors actively looking for promising startups to support.

This casual mixer includes:
- Speed networking sessions
- Founder stories and experiences
- Investor meet-and-greet
- Startup showcase tables
- Refreshments and light bites

Whether you're just starting out or scaling your business, this is the perfect opportunity to expand your network and learn from others on the same journey.
                '''.strip(),
                'event_type': 'in-person',
                'start_date': timezone.now() + timedelta(days=15),
                'end_date': timezone.now() + timedelta(days=15, hours=4),
                'venue_name': 'Impact Hub Accra',
                'venue_address': 'Roman Ridge, Accra, Greater Accra Region, Ghana',
                'contact_email': 'hello@impacthubaccra.com',
                'category': event_categories[3],  # Networking
                'registration_required': True,
                'max_attendees': 100,
                'price': 50.00,
                'currency': 'GHS',
                'is_featured': True,
            },
            {
                'title': 'Free Digital Marketing Workshop',
                'summary': 'Learn essential digital marketing skills to grow your business online. Completely FREE for all participants.',
                'description': '''
Learn essential digital marketing skills to grow your business online. This hands-on workshop is completely FREE and open to all small business owners and aspiring digital marketers.

Workshop Topics:
- Social Media Marketing Fundamentals
- Content Creation Best Practices
- Facebook and Instagram Advertising
- Google My Business Optimization
- Email Marketing Strategies
- Analytics and Performance Tracking

Our expert facilitators will guide you through practical exercises and real-world case studies. Bring your laptop and get ready to start building your digital presence!

Limited seats available - register early to secure your spot.
                '''.strip(),
                'event_type': 'in-person',
                'start_date': timezone.now() + timedelta(days=10),
                'end_date': timezone.now() + timedelta(days=10, hours=5),
                'venue_name': 'Kumasi Business Hub',
                'venue_address': 'Adum, Kumasi, Ashanti Region, Ghana',
                'contact_email': 'info@kumasibusinesshub.com',
                'category': event_categories[2],  # Education
                'registration_required': True,
                'max_attendees': 50,
                'price': 0.00,
                'currency': 'GHS',
                'is_trending': True,
            },
            {
                'title': 'Virtual Webinar: Future of Fintech in Africa',
                'summary': 'Join industry experts for an insightful discussion on the future of financial technology across Africa.',
                'description': '''
Join industry experts for an insightful discussion on the future of financial technology across the African continent, with special focus on Ghana's growing fintech sector.

Featured Speakers:
- CEO of leading Ghanaian mobile money platform
- Financial inclusion expert from World Bank
- Blockchain technology consultant
- Payment systems innovation director

Discussion Topics:
- Mobile Money and Financial Inclusion
- Regulatory Frameworks for Fintech
- Cryptocurrency Adoption in Africa
- Cross-border Payment Solutions
- Investment Opportunities in African Fintech

This virtual event is perfect for fintech professionals, investors, developers, and anyone interested in the intersection of finance and technology in Africa.

Register now and submit your questions in advance!
                '''.strip(),
                'event_type': 'virtual',
                'start_date': timezone.now() + timedelta(days=7),
                'end_date': timezone.now() + timedelta(days=7, hours=2),
                'venue_name': 'Online Event',
                'venue_address': 'Virtual - Zoom Meeting',
                'virtual_meeting_url': 'https://zoom.us/j/fintech-africa-webinar',
                'contact_email': 'events@fintechafrica.com',
                'category': event_categories[1],  # Business
                'registration_required': True,
                'max_attendees': 1000,
                'price': 0.00,
                'currency': 'GHS',
                'is_featured': True,
            },
            {
                'title': 'Ghana Independence Day Cultural Festival',
                'summary': 'Celebrate Ghana\'s rich cultural heritage with traditional music, dance, food, and art from all regions.',
                'description': '''
Celebrate Ghana's rich cultural heritage at our annual Independence Day festival featuring traditional music, dance, food, and art from all regions of Ghana.

Festival Highlights:
- Traditional dance performances from all 16 regions
- Live Highlife and Hiplife music concerts
- Ghanaian food court with regional specialties
- Arts and crafts marketplace
- Cultural exhibitions and displays
- Children's activities and games
- Fashion showcase of traditional and modern Ghanaian wear

This family-friendly event is open to everyone and celebrates the diversity and unity of Ghana. Bring your family and friends for a day of culture, community, and celebration!

Free admission for children under 12.
                '''.strip(),
                'event_type': 'in-person',
                'start_date': timezone.now() + timedelta(days=45),
                'end_date': timezone.now() + timedelta(days=45, hours=8),
                'venue_name': 'Black Star Square',
                'venue_address': 'High Street, Accra, Greater Accra Region, Ghana',
                'contact_email': 'info@ghanaculturalheritage.com',
                'category': event_categories[4],  # Cultural
                'registration_required': False,
                'price': 20.00,
                'currency': 'GHS',
                'is_trending': True,
            },
        ]

        # Create the events
        created_count = 0
        for event_data in events_data:
            # Check if event already exists
            if Event.objects.filter(title=event_data['title']).exists():
                self.stdout.write(self.style.WARNING(f'  Event already exists: {event_data["title"]}'))
                continue

            # Create event
            event = Event.objects.create(
                organizer=organizer,
                status='published',
                published_at=timezone.now(),
                views_count=random.randint(50, 2000),
                registered_count=random.randint(10, min(event_data.get('max_attendees', 100), 100)),
                **event_data
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {event.title}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} events!'))
        self.stdout.write(self.style.SUCCESS('You can now access the events at: http://localhost:8000/api/events/'))