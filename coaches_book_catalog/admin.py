from django.contrib import admin
from .models import Coach, Package, AvailabilitySlot, Location, Review, MessageInquiry, BookingRequest

class PackageInline(admin.TabularInline):
    model = Package
    extra = 1

class AvailabilityInline(admin.TabularInline):
    model = AvailabilitySlot
    extra = 1

class LocationInline(admin.TabularInline):
    model = Location
    extra = 1

@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('name','license_label','verified','city','country')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PackageInline, AvailabilityInline, LocationInline]

admin.site.register(Review)
admin.site.register(MessageInquiry)
admin.site.register(BookingRequest)
