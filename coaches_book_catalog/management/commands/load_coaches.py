import csv
import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from coaches_book_catalog.models import Coach
from scheduler.models import Jadwal  

User = get_user_model()

class Command(BaseCommand):
    help = 'Load data from all_coaches.csv file and create recurring schedules'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting existing Coach data...")
        Coach.objects.all().delete()
        
        self.stdout.write("Deleting existing Jadwal data...")
        Jadwal.objects.all().delete()
        
        self.stdout.write("Deleting existing non-staff/non-superuser User data...")
        User.objects.filter(is_staff=False, is_superuser=False).delete()
        
        file_path = 'all_coaches.csv' 
        count = 0 
        
        self.stdout.write(f"Loading data from {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                possible_start_hours = [9, 11, 14, 16] 
                schedule_duration_hours = 2 
                schedules_per_week = 3
                days_to_generate = 365 
                
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
                            'rate_per_session': 100000 * random.randint(1, 5) 
                        }
                    )
                    
                    
                    chosen_weekdays = random.sample(range(7), schedules_per_week) 
                    chosen_start_hours = random.sample(possible_start_hours, schedules_per_week)
                    
                    schedule_map = dict(zip(chosen_weekdays, chosen_start_hours))
                    
                    start_date = timezone.now().date()
                    
                    jadwal_batch_to_create = [] 
                    
                    for i in range(days_to_generate):
                        current_date = start_date + datetime.timedelta(days=i)
                        current_weekday = current_date.weekday() 
                        
                        if current_weekday in schedule_map:
                            start_hour = schedule_map[current_weekday]
                            
                            if start_hour + schedule_duration_hours <= 23: 
                                jam_mulai = datetime.time(hour=start_hour, minute=0)
                                jam_selesai = datetime.time(hour=start_hour + schedule_duration_hours, minute=0)
                                
                                jadwal_batch_to_create.append(
                                    Jadwal(
                                        coach=coach_obj,
                                        tanggal=current_date,
                                        jam_mulai=jam_mulai,
                                        jam_selesai=jam_selesai,
                                        is_booked=False
                                    )
                                )
                    
                    if jadwal_batch_to_create:
                        Jadwal.objects.bulk_create(jadwal_batch_to_create)
                    
                    
                    count += 1 

            self.stdout.write(self.style.SUCCESS(f'Successfully loaded or updated {count} coach data and created schedules.'))

        except FileNotFoundError:
             self.stdout.write(self.style.ERROR(f'Error: File "{file_path}" not found.'))
        except KeyError as e:
             self.stdout.write(self.style.ERROR(f'Error: Column "{e}" not found in CSV file. Check CSV headers.'))
        except Exception as e:
             self.stdout.write(self.style.ERROR(f'An unexpected error occurred: {e}'))