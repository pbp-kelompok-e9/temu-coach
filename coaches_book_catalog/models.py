from django.db import models

class Coach(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    headline = models.CharField(max_length=200, blank=True)  # ex: "UEFA A Licensed coach"
    bio = models.TextField(blank=True)                       # Coaching Experience, Session Plan
    verified = models.BooleanField(default=False)
    license_label = models.CharField(max_length=120, blank=True)  # "UEFA A Licensed coach"
    experience_years = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    photo_url = models.URLField(blank=True)                  # biar cepat, pakai URL dulu

    def __str__(self):
        return self.name

    @property
    def avg_rating(self):
        agg = self.reviews.aggregate(models.Avg('rating'), models.Count('id'))
        return (agg['rating__avg'] or 0, agg['id'])

class Package(models.Model):
    coach = models.ForeignKey(Coach, related_name='packages', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)                  # ex: "Single Session", "5-Pack"
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.name} - {self.coach.name}'

WEEKDAYS = [(i, d) for i, d in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])]

class AvailabilitySlot(models.Model):
    coach = models.ForeignKey(Coach, related_name='availability', on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=WEEKDAYS)          # 0..6
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True)

    class Meta:
        ordering = ['weekday','start_time']

class Location(models.Model):
    coach = models.ForeignKey(Coach, related_name='locations', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)                  # ex: "West Ham Training Ground"
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f'{self.name} ({self.city})'

class Review(models.Model):
    coach = models.ForeignKey(Coach, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1,6)])
    comment = models.TextField(blank=True)
    author_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class MessageInquiry(models.Model):
    coach = models.ForeignKey(Coach, related_name='inquiries', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class BookingRequest(models.Model):
    STATUS = [('pending','Pending'),('approved','Approved'),('declined','Declined')]
    coach = models.ForeignKey(Coach, related_name='booking_requests', on_delete=models.CASCADE)
    package = models.ForeignKey(Package, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=120)                  # requester
    email = models.EmailField()
    requested_date = models.DateField()
    requested_time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
