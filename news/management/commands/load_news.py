# news/management/commands/load_news.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import random

from news.models import NewsArticle
from tags.models import Category, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Load 5 mock news articles for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating mock news articles...')

        # Create or get admin user as author
        author, created = User.objects.get_or_create(
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
            author.set_password('admin123')
            author.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))

        # Create categories
        categories_data = [
            {'name': 'Politics', 'icon': 'government', 'color': '#CE1126'},
            {'name': 'Business', 'icon': 'briefcase', 'color': '#006B3F'},
            {'name': 'Technology', 'icon': 'cpu', 'color': '#FCD116'},
            {'name': 'Sports', 'icon': 'trophy', 'color': '#CE1126'},
            {'name': 'Entertainment', 'icon': 'music', 'color': '#FCD116'},
        ]

        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_active': True,
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'  Created category: {category.name}')

        # Create tags
        tags_data = [
            'Ghana', 'Accra', 'Kumasi', 'Economy', 'Education',
            'Health', 'Innovation', 'Diaspora', 'Culture', 'Breaking'
        ]

        tags = []
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'is_active': True}
            )
            tags.append(tag)
            if created:
                self.stdout.write(f'  Created tag: {tag.name}')

        # Mock news articles data
        articles_data = [
            {
                'title': 'Ghana Launches New Digital Payment System for Public Services',
                'summary': 'The government has unveiled a comprehensive digital payment platform aimed at streamlining transactions for public services across the country.',
                'content': '''
The Government of Ghana has officially launched a state-of-the-art digital payment system designed to revolutionize how citizens interact with public services. The new platform, developed in partnership with leading fintech companies, will enable seamless electronic payments for utilities, licenses, permits, and other government services.

Minister of Finance, speaking at the launch ceremony in Accra, emphasized that this initiative is part of the government's broader digital transformation agenda. "This platform will reduce bureaucracy, eliminate cash handling risks, and provide citizens with convenient 24/7 access to public services," the minister stated.

The system integrates mobile money, bank cards, and online banking, supporting all major payment providers in Ghana. Early pilot programs in the Greater Accra Region have shown promising results, with transaction times reduced by over 70% compared to traditional payment methods.

Citizens can access the platform through a dedicated mobile app or web portal, with support available in English, Twi, Ga, and Ewe. The government plans to expand the service nationwide over the next six months.
                '''.strip(),
                'category': categories[1],  # Business
                'tags': [tags[0], tags[1], tags[3]],  # Ghana, Accra, Economy
                'is_breaking': True,
                'is_featured': True,
                'location': 'Accra',
                'source': 'Ghana Notice Board',
            },
            {
                'title': 'Tech Startup from Kumasi Secures $2M in Series A Funding',
                'summary': 'A Kumasi-based agricultural technology startup has raised $2 million in Series A funding to expand its innovative farming solutions across West Africa.',
                'content': '''
AgroTech Ghana, a pioneering agricultural technology company based in Kumasi, has successfully secured $2 million in Series A funding from a consortium of local and international investors. The startup, founded in 2021, has developed an AI-powered platform that helps smallholder farmers optimize crop yields and manage resources efficiently.

The funding round was led by Ghana Ventures Capital and included participation from several impact investors focused on agricultural innovation in Africa. The company plans to use the investment to expand its operations to neighboring countries and develop new features for its platform.

AgroTech Ghana's mobile application provides farmers with real-time weather updates, pest alerts, market prices, and expert agricultural advice. The platform currently serves over 50,000 farmers across the Ashanti, Brong-Ahafo, and Northern Regions.

CEO Kwame Osei expressed excitement about the funding: "This investment validates our mission to empower farmers with technology. We're not just building a business; we're transforming agriculture in Ghana and beyond."

The company has already partnered with the Ministry of Food and Agriculture and several agricultural cooperatives. With this new funding, AgroTech Ghana aims to triple its user base within the next year.
                '''.strip(),
                'category': categories[2],  # Technology
                'tags': [tags[0], tags[2], tags[6]],  # Ghana, Kumasi, Innovation
                'is_featured': True,
                'is_trending': True,
                'location': 'Kumasi',
                'source': 'Tech Ghana',
            },
            {
                'title': 'New Educational Initiative Aims to Train 10,000 Youth in Digital Skills',
                'summary': 'A public-private partnership has launched an ambitious program to equip young Ghanaians with essential digital and technical skills for the modern workforce.',
                'content': '''
The Ghana Digital Skills Initiative (GDSI), a collaborative effort between the government and leading technology companies, was officially launched today with the goal of training 10,000 young people in critical digital skills over the next two years.

The program will offer free training in areas including software development, digital marketing, data analysis, cybersecurity, and graphic design. Participants will receive internationally recognized certifications upon completion of their chosen tracks.

Training centers will be established in all 16 regions of Ghana, with the first cohort set to begin in Accra, Kumasi, and Takoradi. The initiative specifically targets unemployed youth aged 18-35, with a commitment to ensure at least 50% female participation.

Minister of Education highlighted the program's importance: "In today's digital economy, these skills are no longer optional—they're essential. This initiative will help bridge the skills gap and create pathways to employment for our youth."

Industry partners including major tech companies and local startups have committed to providing internship opportunities and potential employment for program graduates. The initiative is expected to contribute significantly to Ghana's digital transformation goals and economic growth.
                '''.strip(),
                'category': categories[1],  # Business
                'tags': [tags[0], tags[4], tags[6]],  # Ghana, Education, Innovation
                'is_trending': True,
                'location': 'Multiple Regions',
                'source': 'Ghana Notice Board',
            },
            {
                'title': 'Ghanaian Athletes Shine at West African Championships',
                'summary': 'Team Ghana secured multiple medals at the West African Athletics Championships, showcasing exceptional talent in track and field events.',
                'content': '''
Ghanaian athletes have made the nation proud with outstanding performances at the 2026 West African Athletics Championships held in Abuja, Nigeria. The team brought home a total of 12 medals, including 4 golds, 5 silvers, and 3 bronzes.

Standout performances came from sprinter Janet Amponsah, who won gold in both the 100m and 200m events, setting a new championship record in the 200m with a time of 22.45 seconds. Long-distance runner Emmanuel Mensah also impressed, taking gold in the 5000m race.

The men's 4x100m relay team delivered a thrilling victory in the final event of the championships, edging out strong competition from Nigeria and Senegal. Team captain Kofi Asante attributed their success to rigorous training and unwavering team spirit.

Athletics Federation president praised the team's dedication: "These results demonstrate that Ghana has world-class athletic talent. We're committed to providing our athletes with the resources they need to compete at the highest levels."

The performance has boosted Ghana's preparations for upcoming continental championships and has inspired young athletes across the country. Several team members are now being scouted by international athletic clubs.
                '''.strip(),
                'category': categories[3],  # Sports
                'tags': [tags[0]],  # Ghana
                'location': 'Abuja, Nigeria',
                'source': 'Sports Ghana',
            },
            {
                'title': 'Ghana Diaspora Festival 2026 Set to Celebrate Cultural Heritage',
                'summary': 'The annual Ghana Diaspora Festival will bring together thousands of Ghanaians from around the world to celebrate culture, heritage, and economic opportunities.',
                'content': '''
Preparations are in full swing for the 2026 Ghana Diaspora Festival, scheduled to take place in Accra from July 15-21. The week-long celebration is expected to attract over 5,000 participants from the United States, United Kingdom, Canada, and other countries with significant Ghanaian populations.

This year's festival theme, "Connecting Roots, Building Futures," emphasizes both cultural celebration and economic engagement. The program includes traditional music and dance performances, art exhibitions, business networking events, and investment forums.

The festival will feature performances by top Ghanaian musicians and cultural groups, showcasing traditional drumming, highlife music, and contemporary Afrobeats. A special diaspora marketplace will allow attendees to explore business opportunities and learn about investing in Ghana.

Minister of Tourism emphasized the festival's dual purpose: "This event is not just about celebrating our rich culture—it's also about strengthening economic ties between Ghana and our diaspora community. We want our brothers and sisters abroad to see Ghana as a place to invest, create, and thrive."

Special programs have been arranged including heritage tours to historical sites, a youth leadership summit, and a technology and innovation expo. The festival has become a major annual event since its inception in 2019, contributing significantly to tourism and foreign direct investment.
                '''.strip(),
                'category': categories[4],  # Entertainment
                'tags': [tags[0], tags[1], tags[7], tags[8]],  # Ghana, Accra, Diaspora, Culture
                'is_featured': True,
                'location': 'Accra',
                'source': 'Ghana Notice Board',
            },
        ]

        # Create the articles
        created_count = 0
        for article_data in articles_data:
            # Extract tags and category
            article_tags = article_data.pop('tags', [])
            
            # Check if article already exists
            if NewsArticle.objects.filter(title=article_data['title']).exists():
                self.stdout.write(self.style.WARNING(f'  Article already exists: {article_data["title"]}'))
                continue

            # Create article
            article = NewsArticle.objects.create(
                author=author,
                published_by=author,
                status='published',
                published_at=timezone.now() - timedelta(hours=random.randint(1, 48)),
                views_count=random.randint(100, 5000),
                likes_count=random.randint(10, 500),
                comments_count=random.randint(5, 100),
                shares_count=random.randint(2, 50),
                bookmarks_count=random.randint(5, 200),
                allow_comments=True,
                **article_data
            )

            # Add tags
            article.tags.set(article_tags)
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {article.title}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} news articles!'))
        self.stdout.write(self.style.SUCCESS('You can now access the news at: http://localhost:8000/api/articles/'))