import csv
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model # <-- Gunakan ini
from coaches_book_catalog.models import Coach

User = get_user_model()

class Command(BaseCommand):
    help = 'Load data from all_coaches.csv file'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting existing Coach data...")
        Coach.objects.all().delete()
        
        self.stdout.write("Deleting existing non-staff/non-superuser User data...")
        User.objects.filter(is_staff=False, is_superuser=False).delete() 
        
        file_path = 'all_coaches.csv' 
        count = 0 
        
        self.stdout.write(f"Loading data from {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    username = row['name'].replace(' ', '').lower() + str(count) 
                    
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': f"{username}@example.com", 
                            'user_type': 'coach'
                            } 
                    )
                    
                    if not created and user.user_type != 'coach':
                        user.user_type = 'coach'
                        user.save()
                        self.stdout.write(self.style.WARNING(f'Updated existing user {username} to coach.'))
                        
                    if created:
                        user.set_password('password123') 
                        user.save()

                    coach_obj, coach_created = Coach.objects.update_or_create(
                        user=user, 
                        defaults={
                            'name': row['name'],
                            'age': int(row['age']),
                            'citizenship': row['citizenship'],
                            'club': row['club'],
                            'license': row['coaching_licence'], 
                            'preffered_formation': row['preffered_formation'],
                            'average_term_as_coach': float(row['avg_term_as_coach'].replace(' Years', '')),
                            'description': f"Seorang pelatih berpengalaman dari {row['club']}.",
                            'rate_per_session': 1000000 * random.randint(0, 5)
                        }
                    )
                    count += 1 

            self.stdout.write(self.style.SUCCESS(f'Successfully loaded or updated {count} coach data'))

        except FileNotFoundError:
             self.stdout.write(self.style.ERROR(f'Error: File "{file_path}" not found.'))
        except KeyError as e:
             self.stdout.write(self.style.ERROR(f'Error: Column "{e}" not found in CSV file. Check CSV headers.'))
        except Exception as e:
             self.stdout.write(self.style.ERROR(f'An unexpected error occurred: {e}'))