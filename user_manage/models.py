import datetime
import re

from django.db import models
from django.contrib.auth.models import User

from django.contrib.sessions.models import Session



def profile_path(instance, filename):
	return f"images/uploads/{instannce.user.name}/{filename}"

def dinning_img_path(instance, filename):
	return f"images/listing_imgs/{instannce.user.name}/{filename}"

def svg_img_validation(value):
	return True


def get_kitchen_name():
	return f'SonchiKitchen-{ len(HostProperty.objects.all()) + 1 }'

# # Create your models here.
# class SessionManager(models.Model):
# 	user_id = models.ForeignKey('User', on_delete=models.CASCADE)
# 	guest_id = models.ForeignKey('Guest', on_delete=models.CASCADE)
# 	host_id = models.ForeignKey('Host', on_delete=models.CASCADE)
# 	token = models.ForeignKey(Session, on_delete=models.CASCADE)



class Host(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	profile = models.ForeignKey('HostProfile', on_delete=models.CASCADE)
	fssai_no = models.CharField(max_length=15)	
	active = models.BooleanField(default=True)
	properties = models.ManyToManyField('HostProperty')
	answers = models.ManyToManyField('Answer')
	# registration_time = models.DateTimeField(default=datetime.datetime.now())


class Guest(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	profile = models.ForeignKey('SonchiUserProfile', on_delete=models.CASCADE)
	active = models.BooleanField(default=True)
	bookings = models.ManyToManyField('EventBooking', blank=True)

	@classmethod
	def get_attributes(cls):
		return ['user', 'profile', 'active', 'bookings']
	

class SonchiUserProfile(models.Model):
	identity_verified = models.BooleanField(default=False)
	email_verified = models.BooleanField(default=False)
	mobile_verified = models.BooleanField(default=False)
	user_type = models.BooleanField(default=False)  # True - Host, False - Guest
	
	identity_number = models.CharField(max_length=50, default='')
	mobile_number = models.CharField(max_length=15, default='')
	address = models.CharField(max_length=50, blank=True)
	about = models.CharField(max_length=500, blank=True)
	position_title = models.CharField(max_length=20, default='')
	work = models.CharField(max_length=20, default='')
	school = models.CharField(max_length=50, default='')
	fav_time_spend = models.CharField(max_length=50, default='')
	fun_fact = models.CharField(max_length=50, default='')
	biography_title = models.CharField(max_length=50, default='')
	languages = models.CharField(max_length=50, default='')
	about_home = models.CharField(max_length=50, default='')
	community = models.CharField(max_length=50, default='')
	guest_message = models.CharField(max_length=50, default='')

	profile_img = models.ImageField(upload_to='images/guest-profile/', blank=True)

	hobbies = models.ManyToManyField('Answer', related_name='hobbies')
	dinning_profiles = models.ManyToManyField('Answer', related_name='dinning_profiles')
	# birthday = models.DateTimeField(default=datetime.datetime.now())
	# registration_date = models.DateTimeField(default=datetime.datetime.now())

	def get_json(self):
		obj = {}
		attribute_keys = [ 'identity_verified', 'identity_number', 'email_verified', 'mobile_number', 
			'mobile_verified', 'user_type',	'address', 'about', 'position_title', 
			'work', 'school', 'fav_time_spend', 'fun_fact', 'biography_title', 
			'languages', 'about_home', 'community', 'guest_message'
		]
		for key in attribute_keys:
			obj[key] = getattr(self, key)

		return obj

	@classmethod
	def get_attributes(cls):
		return [ 'identity_verified', 'identity_number', 'email_verified', 'mobile_number', 
			'mobile_verified', 'user_type',	'address', 'about', 'position_title', 
			'work', 'school', 'fav_time_spend', 'fun_fact', 'biography_title', 
			'languages', 'about_home', 'community', 'guest_message'
		]


class HostListingImages(models.Model):
	image = models.ImageField(upload_to="images/listings/")
	uploaded_by = models.ForeignKey('Host', on_delete=models.CASCADE)

	

class HostProfile(models.Model):
	identity_verified = models.BooleanField(default=False)
	email_verified = models.BooleanField(default=False)
	mobile_verified = models.BooleanField(default=False)
	mobile_number = models.CharField(max_length=15, unique=True)
	gov_id_number = models.CharField(max_length=50, unique=True)
	profile_title = models.CharField(max_length=50)
	about = models.CharField(max_length=500)	
	facebook = models.URLField()
	twitter = models.URLField()
	instagram = models.URLField()
	youtube = models.URLField()
	profile_img = models.ImageField(upload_to='images/host-profile/')
	certificate_image = models.ImageField('images/host-certificate/')
	

	@classmethod
	def get_attributes(cls):
		return ['identity_verified', 'gov_id_number', 'mobile_number']

	def get_json(self):
		return {'mobile_number': self.mobile_number}



class HostProperty(models.Model):
	kitchen_name = models.CharField(unique=True, max_length=50, default=get_kitchen_name)
	rate_per_guest = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
	number_of_seats = models.PositiveIntegerField(default=0)
	description = models.CharField(max_length=500)
	venue = models.CharField(max_length=200)
	ambiances = models.ManyToManyField('Ambiance', related_name='ambiances')
	twd = models.ForeignKey('TWD', on_delete=models.SET_NULL, null=True)
	amenities = models.ManyToManyField('Amenity')
	additional_info = models.ForeignKey('ListingDescription', on_delete=models.SET_NULL, null=True, related_name='additional_info')
	images = models.ManyToManyField('HostListingImages')
	events = models.ManyToManyField('Event')
	cultural_insights = models.ForeignKey('CulturalInsightRule', on_delete=models.CASCADE, blank=True, null=True)
	address_line = models.CharField(max_length=50, null=True)
	address_street = models.CharField(max_length=50, null=True)
	address_city = models.CharField(max_length=50, null=True)
	address_pincode = models.CharField(max_length=6, null=True)
	address_state = models.CharField(max_length=10, null=True)
	address_lat = models.CharField(max_length=10, null=True)
	address_lng = models.CharField(max_length=10, null=True)

	@classmethod
	def get_attributes(cls):
		return ['kitchen_name', 'rate_per_guest', 'number_of_seats', 'description', 'venue', 'listing_description', 'ambiance', 'three_word_description', 'amenities', 'additional_info', 'images', 'events']

class ListingDescription(models.Model):
	cultural_insights = models.ForeignKey('CulturalInsightRule', on_delete=models.CASCADE, related_name="cultural_insights")
	house_rules = models.ForeignKey('CulturalInsightRule', on_delete=models.CASCADE, related_name='house_rules')
	security_safety = models.ForeignKey('CulturalInsightRule', on_delete=models.CASCADE, related_name='sacurity_safety')


class CulturalInsightRule(models.Model):
	description = models.CharField(max_length=500, blank=True, null=True)
	headings = models.CharField(max_length=500, blank=True, null=True)
	detail_text = models.CharField(max_length=1000, blank=True, null=True)


class Ambiance(models.Model):
	amb_type = models.SlugField()
	title = models.CharField(max_length=100)
	description =models.CharField(max_length=200)

class TWD(models.Model):
	certificate = models.CharField(max_length=100)
	coocking_aura = models.CharField(max_length=100)
	test = models.CharField(max_length=100)

class Amenity(models.Model):
	# svg = models.CharField(max_length=10000)
	title = models.CharField(max_length=200)
	category = models.CharField(max_length=100)



class Event(models.Model):
	date = models.DateField()
	meals = models.ManyToManyField('Meal')


class Meal(models.Model):
	name = models.CharField(max_length=50)
	start_time = models.TimeField()
	end_time = models.TimeField()
	menu = models.ForeignKey('Menu', on_delete=models.CASCADE)

class Menu(models.Model):
	title = models.CharField(max_length=50)
	diet = models.ForeignKey('Answer', related_name="diet", on_delete=models.CASCADE)
	service_offer = models.ForeignKey('Answer', related_name="services_offer", on_delete=models.CASCADE)
	cuisine = models.ForeignKey('Answer', related_name="cuisine", on_delete=models.CASCADE)
	welcome_drinks = models.ManyToManyField('Answer', related_name='welcome_drinks')
	star_dish = models.ManyToManyField('Answer', related_name='star_dish')
	soothing_soups = models.ManyToManyField('Answer', related_name='soothing_soups')
	tantalizing_starters = models.ManyToManyField('Answer', related_name='tantalizing_starters')
	mains = models.ManyToManyField('Answer', related_name='mains')
	sweet_endings = models.ManyToManyField('Answer', related_name='sweet_endings')
	guest_note = models.CharField(max_length=200)



class EventBooking(models.Model):
	location = models.ForeignKey('HostProperty', on_delete=models.SET_NULL, null=True)
	event_guest = models.ForeignKey('Guest', on_delete=models.SET_NULL, null=True)
	paid = models.BooleanField(default=False)
	active = models.BooleanField(default=True)
	status = models.CharField(max_length=20)
	event = models.ManyToManyField('Event')
	number_of_people = models.PositiveIntegerField()
	

	def to_json(self):
		return { 
			'location': self.location,
			'event_guest': self.event_guest,
			'pain' : self.paid,
			'status': self.status,
			'active': self.active,
			'no_people': self.no_people, 
			'about': self.about,
			'time': self.time
		}




class Question(models.Model):
	question_number = models.PositiveIntegerField(blank=False, null=False)
	question_text = models.CharField(max_length=200, blank=False, null=False)
	# options = models.ManyToManyField('Answer', related_name="options")
	question_code = models.SlugField(unique=True)

	def __repr__(self):
		return f'{self.question_number}-{self.question_code}'

	def __str__(self):
		return f'{self.question_code}'

	@classmethod
	def get_attributes(cls):
		return ['question_number', 'question_code', 'question_text']


class Answer(models.Model):
	question = models.ForeignKey('Question', on_delete=models.CASCADE)
	image = models.ImageField(upload_to="images/answer/", blank=True)
	image_data = models.TextField(max_length=5000)
	ans_text = models.CharField(max_length=50)
	option_number = models.PositiveIntegerField()
	sub_options = models.TextField(max_length=500, null=True, blank=True )

	@classmethod
	def get_attributes(cls):
		return ['question', 'image', 'ans_text', 'option_number', 'sub_options']


class Reviews(models.Model):
	review_guest = models.ForeignKey('Guest', on_delete=models.CASCADE)
	review_text = models.CharField(max_length=500)
	review_host = models.ForeignKey('Host', on_delete=models.CASCADE, default=1)
	star = models.DecimalField(decimal_places=1, max_digits=2)
	date = models.DateField()



class MessagesContactUs(models.Model):
	full_name = models.CharField(max_length=20)
	email = models.EmailField()
	mobile_number = models.PositiveIntegerField()
	msg = models.CharField(max_length=500)

	def __repr__(self):
		return f'{self.full_name}'

	def __str__(self):
		return f'{self.full_name}'



# the number of solution of the equation 
# sin_x = (cos_x)2 
# in interval (0, 10) is