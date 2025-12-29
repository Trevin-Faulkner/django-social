from django.core.management.base import BaseCommand
from django.utils import timezone

from social.models import Connection, Conversation, Experience, Message, User


class Command(BaseCommand):
    help = "Seed demo data for the ConnectPro experience."

    def handle(self, *args, **options):
        users = [
            {
                'username': 'sarah',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah.j@example.com',
                'role': User.ROLE_DEVELOPER,
                'membership_plan': User.PLAN_PLUS,
                'headline': 'Full Stack Developer | React & Node.js Expert',
                'skills': 'React,Node.js,TypeScript,PostgreSQL,AWS',
                'location': 'San Francisco, CA',
            },
            {
                'username': 'alex',
                'first_name': 'Alex',
                'last_name': 'Chen',
                'email': 'alex@example.com',
                'role': User.ROLE_CLIENT,
                'membership_plan': User.PLAN_PRO,
                'headline': 'Tech Entrepreneur | Looking for Mobile App Developers',
                'skills': 'iOS,Android,Product Design',
                'location': 'New York, NY',
            },
            {
                'username': 'maria',
                'first_name': 'Maria',
                'last_name': 'Garcia',
                'email': 'maria@example.com',
                'role': User.ROLE_CLIENT,
                'membership_plan': User.PLAN_FREE,
                'headline': 'Startup Founder | Need Full Stack Developer',
                'skills': 'React,Node.js,AWS',
                'location': 'Austin, TX',
            },
            {
                'username': 'james',
                'first_name': 'James',
                'last_name': 'Wilson',
                'email': 'james@example.com',
                'role': User.ROLE_CLIENT,
                'membership_plan': User.PLAN_PLUS,
                'headline': 'Product Manager | Hiring for SaaS Project',
                'skills': 'Python,Django,PostgreSQL',
                'location': 'San Francisco, CA',
            },
            {
                'username': 'emily',
                'first_name': 'Emily',
                'last_name': 'Taylor',
                'email': 'emily@example.com',
                'role': User.ROLE_CLIENT,
                'membership_plan': User.PLAN_FREE,
                'headline': 'E-commerce Owner | Looking for Web Developer',
                'skills': 'Shopify,WordPress,SEO',
                'location': 'Los Angeles, CA',
            },
        ]

        created_users = {}
        for data in users:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={k: v for k, v in data.items() if k != 'username'},
            )
            if created:
                user.set_password('password123')
                user.save()
            created_users[data['username']] = user

        sarah = created_users['sarah']
        Experience.objects.get_or_create(
            user=sarah,
            title='Senior Developer',
            company='Tech Innovations Inc',
            start_year=2021,
            defaults={'description': 'Leading development of enterprise applications'},
        )
        Experience.objects.get_or_create(
            user=sarah,
            title='Full Stack Developer',
            company='StartupXYZ',
            start_year=2018,
            end_year=2021,
            defaults={'description': 'Built and scaled web applications'},
        )

        # Connections from Sarah to clients
        for key in ['alex', 'maria', 'james', 'emily']:
            Connection.objects.get_or_create(requester=sarah, receiver=created_users[key])

        # Sample conversation with Alex
        convo = Conversation.objects.filter(participants=sarah).filter(participants=created_users['alex']).first()
        if not convo:
            convo = Conversation.objects.create()
            convo.participants.add(sarah, created_users['alex'])

        if not convo.messages.exists():
            Message.objects.create(
                conversation=convo,
                sender=created_users['alex'],
                body="Hi! I saw your profile and I'm impressed with your work.",
                created_at=timezone.now(),
            )
            Message.objects.create(
                conversation=convo,
                sender=sarah,
                body="Thank you! I'd love to hear more about your project.",
                created_at=timezone.now(),
            )
            Message.objects.create(
                conversation=convo,
                sender=created_users['alex'],
                body="We're building a mobile app for our startup. Need a React Native developer.",
                created_at=timezone.now(),
            )
            Message.objects.create(
                conversation=convo,
                sender=sarah,
                body="That sounds interesting! Could you share more details?",
                created_at=timezone.now(),
            )

        self.stdout.write(self.style.SUCCESS('Demo data ready. Users created with password "password123".'))
