from django.contrib import admin

from .models import Guest, Host, HostProfile
from .models import Question, Answer, HostProperty, HostListingImages
# Register your models here.


admin.site.register(Guest)
admin.site.register(Host)
admin.site.register(HostProfile)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(HostProperty)
admin.site.register(HostListingImages)
