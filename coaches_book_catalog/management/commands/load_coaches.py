import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from coaches_book_catalog.models import Coach

class Command(BaseCommand):
    help = 'Load data from all_coaches.csv file'

    def handle(self, *args, **kwargs):
        Coach.objects.all().delete()
        User.objects.filter(is_staff=False).delete() 
        
        file_path = 'all_coaches.csv' 
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                username = row['name'].replace(' ', '').lower()
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'password': 'password123'} 
                )

                Coach.objects.create(
                    user=user,
                    name=row['name'],
                    age=int(row['age']),
                    citizenship=row['citizenship'],
                    club=row['club'],
                    license=row['coaching_licence'],
                    preffered_formation=row['preffered_formation'],
                    average_term_as_coach=float(row['avg_term_as_coach'].replace(' Years', '')),
                    description=f"Seorang pelatih berpengalaman dari {row['club']}.",
                    rate_per_session=500000.00 
                )

        self.stdout.write(self.style.SUCCESS('Successfully loaded coach data'))