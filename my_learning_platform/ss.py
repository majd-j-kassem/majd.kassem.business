from django.contrib.sites.models import Site

# This will create a Site object with id=1 if it doesn't exist,
# or update its domain and name if it does.
site, created = Site.objects.get_or_create(
    pk=1,
    defaults={'domain': '127.0.0.1:8000', 'name': 'My Learning Platform'}
)
if not created:
    site.domain = '127.0.0.1:8000'
    site.name = 'My Learning Platform'
    site.save()
    print("Existing Site object updated.")
else:
    print("New Site object created.")

print(f"Current Site object: ID={site.pk}, Domain={site.domain}, Name={site.name}")