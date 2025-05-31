from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError

from .models import SonchiUserProfile, HostProfile, Host, Guest, Reviews, EventBooking
from .models import Question, Answer, HostProperty, HostListingImages, Ambiance, TWD, Amenity
from .models import ListingDescription, CulturalInsightRule

from .forms import QuestionForm, AnswerForm, GuestForm

import json, datetime, base64
from functools import reduce





# Create your views here.
def check_login_status(request):
	try:
		session = Session.objects.get(session_key=request.GET.get('session_key'))
	except:
		session = None
	finally:
		return JsonResponse({ 'status': True if session else False })


def verify_session(request):
	try:
		session = Session.objects.get(session_key=request.GET.get('session_key'))
	except ObjectDoesNotExist :
		return JsonResponse({'error': True, 'message': 'session not found, please login again.'})
	if session :
		host = Host.objects.none()
		guest = Guest.objects.none()
		reviews = Reviews.objects.none()
		profile = SonchiUserProfile.objects.none()
		user = User.objects.get(id=request.GET.get('user_id'))

		try:			
			host = Host.objects.filter(user=user)[0]
			profile = host.profile
			reviews = Reviews.objects.filter(review_host=host)
		except:
			guest = Guest.objects.filter(user=user)[0]
			profile = guest.profile
			reviews = Reviews.objects.filter(review_guest=guest)

		return JsonResponse({ 
			**profile.get_json(),
			'is_admin' : user.is_staff,
			'is_guest'	: True if guest else False,
			'is_host' : True if host else False,
			'profile_img' : profile.profile_img.url if profile.profile_img else '',
			'name' : f'{user.first_name} {user.last_name}',
			'total_reviews' :  len(reviews) ,		
			'reviews' : [{
				'r_img': r.review_host.profile_img,
				'r_name': f'{r.review_host.user.first_name} {r.review_host.user.last_name}',
				'r_text' : r.review_text
			} for r in reviews]

			# 'hobbies_array' : [{'h_img': h.img, 'h_title': h.title} for h in profile.hobbies.all()],
			# 'dinnings' : [{
			# 	'dine_img': d.img,
			# 	'dine_title': d.title,
			# 	'dine_desc' : d.description
			# } for d in profile.dinning_profiles.all()],
			# born: profile.birthday,
			# registration_date: profile.registration_date,
		})

	else :
		return JsonResponse({'status': False, 'error': 'unverified request'})




@csrf_exempt
def login_user(request, *args, **kwargs):
	if request.method == "POST":
		# print(request.headers)
		try:
			inputs = json.loads(request.body)
			username = inputs.get('email').split('@')[0]
			password = inputs.get('password')
		except:
			username = request.POST.get('email').split('@')[0]
			password = request.POST.get('password')

		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			# print(dir(request.session))
			guest, host = None, None

			try:
				host = Host.objects.get(user=user, active=True)
				profile = host.profile
			except:
				guest = Guest.objects.get(user=user, active=True)
				profile = guest.profile
			
			print({
				'user_id': user.id, 
				'session_key' : request.session.session_key,
				'profile_id': profile.id,
				'guest_id': guest.id if guest else None,
				'host_id': host.id if host else None,
				'listing_id': host.properties.first().id if host else None
			})
			return JsonResponse({
				'user_id': user.id, 
				'session_key' : request.session.session_key,
				'profile_id': profile.id,
				'guest_id': guest.id if guest else None,
				'host_id': host.id if host else None,
				'listing_id': host.properties.first().id if host else None
			})
		else:
			return HttpResponseForbidden('Invalid credentials...!')

	return render(request, 'login.html', {})



@csrf_exempt
def signup(request):
	inputs = json.loads(request.body)
	user = User.objects.create_user(
		username = inputs.get('email').split('@')[0],
		email = inputs.get('email'),
		first_name = inputs.get('name').split(' ')[0],
		last_name = inputs.get('name').split(' ')[1]

	)
	user.set_password(inputs.get('password'))
	user.save()
	login(request, user)

	profile = SonchiUserProfile.objects.create(
		mobile_number = inputs.get('number'),
		user_type = False
	)
	profile.save()

	guest = Guest(user=user)
	guest.profile = profile
	guest.save()
	print("signUP database process complete: ", user, profile, guest)
	return JsonResponse({
		'user_id': user.id, 
		'session_key' : request.session.session_key,
		'profile_id': profile.id,
		'guest_id': guest.id
	})


def logout_user(request):
	session = Session.objects.get(session_key=request.GET.get('session_key'))
	session.delete()

	return JsonResponse({
		'user_id': None, 
		'session_key' : None,
		'profile_id': None,
		'guest_id': None,
		'host_id': None
	})



@csrf_exempt
def update_profile_data(request, *args, **kwargs):
	inputs = json.loads(request.body)
	if request.method == 'POST':
		profile = SonchiUserProfile.objects.get(id=profile_id)
		profile.identity_number = inputs['identity_number']
		profile.mobile_number = inputs['mobile_number']
		profile.address = inputs['address']
		profile.about = inputs['about']
		profile.position_title = inputs['position_title']
		profile.work = inputs['work']
		profile.school = inputs['school']
		profile.fav_time_spend = inputs['fav_time_spend']
		profile.fun_fact = inputs['fun_fact']
		profile.biography_title = inputs['biography_title']
		profile.languages = inputs['languages']
		profile.about_home = inputs['about_home']
		profile.community = inputs['community']
		profile.guest_message = inputs['guest_message']
		profile.profile_img = inputs['profile_img']

		profile.save()

		return JsonResponse({'data': profile.get_json()})
	else:
		return HttpResponseNotAllowed()



@csrf_exempt
def host_onboard(request):
	profile = None
	user = User.objects.get(id=request.GET.get('user_id'))
	guest = Guest.objects.get(id=request.GET.get('guest_id'))	# print(request.body)	# print(request.POST)	# print(request)

	host_inputs = json.loads(request.body)	# print("host onboard", host_inputs)

	session = Session.objects.get (session_key=request.GET.get('session_key'))
	if session and guest and (guest.user == user):
		guest = Guest.objects.get(user=user)
		try:
			profile = HostProfile.objects.filter(gov_id_number = f'{user.first_name}{guest.profile.mobile_number}', mobile_number = guest.profile.mobile_number)[0]
		except:
			profile = HostProfile.objects.create(
				profile_title = "",
				mobile_number = guest.profile.mobile_number,
				gov_id_number = f'{user.first_name}{guest.profile.mobile_number}',
				about = "",
				facebook = "",
				twitter = "",
				instagram = "",
				youtube = "",
				# certificate_image = request.FILES.get('certificate_image')
			)
			profile.save()

		listing = HostProperty(
			rate_per_guest = 0.0,
			number_of_seats = 0,
			description = '',
			venue = json.dumps(host_inputs.get('coordinates'))
		)
		listing.save()

		try:
			host = Host.objects.create(
				user=user, 
				profile=profile, 
				fssai_no=host_inputs.get('fssai_no'),
				# registration_time=datetime.datetime.now()
			)
			host.save()
		except IntegrityError as err:
			host = Host.objects.get(user=user)
		finally:
			for ans in host_inputs.get('answers'):
				try:
					ans = Answer.objects.filter(ans_text=ans).first()
					host.answers.add(ans)
					host.save()
				except:
					print("Ans not found :", ans)

			guest.active = False
			guest.save()

		print("host created: ", host.id)
		for i, img in enumerate(host_inputs.get('photos')):
			print("img: ", len(img))
			name = host_inputs.get('files')[i]
			data = base64.b64decode(img.split(',')[1])

			file = open(f'static/images/Listings/{name}', 'wb+')
			file.write(data)
			file.close()

			hli = HostListingImages.objects.create(image=name, uploaded_by=host)
			hli.save()
			listing.images.add(hli)

		listing.save()
		host.properties.add(listing)
		host.save()
		return JsonResponse({
			'user_id': user.id, 
			'session_key' : session.session_key,
			'profile_id': profile.id,
			'host_id': host.id,
			'listing_id': listing.id,
			# 'guest_id': '',
		})
	else:
		return HttpResponseNotAllowed()


def update_record(model, max_len, query_set, inputs):
	if len(query_set) > max_len:
		for amb in query_set[max_len:]:
			obj = model.objects.get(id=amb.id)
			obj.delete()
	obj_list = []
	for i, a in enumerate(inputs):
		try:
			obj = model.objects.get(id=query_set[i].id)
			for key, value in a.items():
				setattr(obj, key, value)
			obj.save()
		except:
			obj = model.objects.create(**a)
			obj.save()
		obj_list.append(obj)
	return obj_list


@csrf_exempt
def host_update(request):
	success = False
	print(request.GET.get('profile_id'), request.GET.get('user_id'), request.GET.get('host_id'), request.GET.get('listing_id'))
	profile = HostProfile.objects.get(id=request.GET.get('profile_id'))
	user = User.objects.get(id=request.GET.get('user_id'))
	host = Host.objects.get(id=request.GET.get('host_id'))
	listing = HostProperty.objects.get(id=request.GET.get('listing_id'))

	host_inputs = json.loads(request.body)
	# print("host onboard", host_inputs)

	session = Session.objects.get (session_key=request.GET.get('session_key'))
	if (request.method=='POST') and session and host and profile and (host.user == user) and (host.profile == profile):		
		if (host_inputs.get('section') == 'ABOUT'):
			profile.about = host_inputs.get('aboutText')
			
			media = ['facebook', 'twitter', 'instagram', 'youtube']

			for i, link in enumerate(host_inputs.get('socialMediaLinks')):
				setattr(profile, media[i], link)

			# profile.facebook = host_inputs.get('socialMediaLinks')[0]
			# profile.twitter = host_inputs.get('socialMediaLinks')[1]
			# profile.instagram = host_inputs.get('socialMediaLinks')[2]
			# profile.youtube = host_inputs.get('socialMediaLinks')[3]
			profile.save()

			ci = listing.cultural_insights if listing.cultural_insights else None
			if ci:
				ci.description = host_inputs.get('culturalInsights').get('description')
				ci.headings = '\n'.join(host_inputs.get('culturalInsights').get('headings'))
				ci.detail_text = '\n'.join(host_inputs.get('culturalInsights').get('detail_text'))
				ci.save()
				success = True
			else:
				ci = CulturalInsightRule(description=host_inputs.get('culturalInsights').get('description'),  headings = '\n'.join(host_inputs.get('culturalInsights').get('headings')), detail_text = '\n'.join(host_inputs.get('culturalInsights').get('detail_text')))
				ci.save()
				listing.cultural_insights = ci
				listing.save()
				success = True

		elif (host_inputs.get('section') == 'VENUE'):
			for key, value in host_inputs.get('location').items():
				print(key, ':', value)
				setattr(listing, f'address_{key}', value)
			listing.save()
			success = True


		elif (host_inputs.get('section') == 'AMENITIES'):
			amenity_categories = ['Lift & Staircase', 'Dining Space', 'Scenic View', 'Kitchen Amenities', 'Outdoor Space', 'Space for Kids and Pets', 'Parking Space', 'Games console', 'Additional Amenities']
			lst_amen = listing.amenities.all().order_by('id')
			
			amens_matrix = []
			for i, amens in enumerate(host_inputs.get('amenities')):
				for a in amens:
					amens_matrix.append({'title': a, 'category': amenity_categories[i]})
			
			for amen in amens_matrix:
				try:
					obj = Amenity.objects.filter(**amen)[0]
				except:
					obj = Amenity.objects.create(**amen)
				listing.amenities.add(obj)
				listing.save()
				success = True

		elif (host_inputs.get('section') == 'AMBIANCE'):
			amb_types = ['DINE', 'LIGHT', 'EXPERIANCE']
			lst_amb = listing.ambiances.all().order_by('id')
			
			ambs = [{'title': a[0], 'description': a[1], 'amb_type': amb_types[i]} for i, a in enumerate(host_inputs.get('ambiances')[:3])]
			obj = update_record(Ambiance, 3, lst_amb, ambs)
			if len(obj) :
				listing.ambiances.add(*obj)
				listing.save()
				success = True

		elif (host_inputs.get('section') == 'ADDITIONAL_INFO'):
			info_headings = ['HOUSE_RULE', 'SECURITY_SAFETY', 'CANCELLATION_CHANGES']
			model_attrs = [ 'house_rules', 'security_safety', 'cultural_insights']

			info = [{'description': info_headings[i], 'detail_text': '\n'.join(rule)} for i, rule in enumerate(host_inputs.get('info'))]

			ci = None
			for i, info_item in enumerate(host_inputs.get('info')):
				try:
					cir_id = getattr(getattr(listing.additional_info, model_attrs[i]), id)
					hr = CulturalInsightRule.objects.get(id=cir_id)
					for key, value in info[i]:
						setattr(hr, key, value)
					hr.save()
					success = True
				except:
					ci = ci if ci else ListingDescription()
					cir = CulturalInsightRule.objects.create(**info[i])
					setattr(ci, model_attrs[i], cir)

			if ci :
				ci.save()
				listing.additional_info = ci
				listing.save()
				success = True

		elif (host_inputs.get('section') == 'TWD'):
			twd = host_inputs.get('twdData')
			inps = {'certificate': twd[0], 'coocking_aura': twd[1], 'test': twd[2]}

			try:
				obj = TWD.objects.get(id=listing.twd.id)
				for key, value in inps.items():
					setattr(obj, key, value)
				obj.save()
			except : 
				obj = TWD.objects.create(**inps)
				listing.twd = obj
				listing.save()
				obj.save()
			success = True
		
		return JsonResponse({
			'success': success,
			'host_id': host.id,
		})
	else:
		return HttpResponseNotAllowed()


@login_required(login_url='/admin/login/')
def admin_dashboard(request):
	context = {		
		'guests': len(Guest.objects.all()),
		'hosts': len(Host.objects.all()),
		'questions': len(Question.objects.all()),
		'answers': len(Answer.objects.all())
	}
	return render(request, 'admin_dashboard.html', context=context)


def to_base64(image_file):
	string = str()
	with image_file.open() as imf:
		string = base64.b64encode(imf.read())
	return string

@login_required(login_url='/admin/login/')
def admin_users(request):
	model = None
	objects = None
	form = None
	title = str()
	headings = list()

	match request.path.split('/')[-1].strip():
		case 'users':
			model = User
			title = 'Users'
			objects = User.objects.all().filter(is_staff=False)
			headings = ['username', 'email']
		case 'questions':
			model = Question
			title = 'Questions'
			form = QuestionForm
			headings = Question.get_attributes()
		case 'answers':
			model = Answer
			title = 'Answers'
			form = AnswerForm
			headings = Answer.get_attributes()
		case 'hosts':
			model = Host
			title = 'Hosts'
			headings = ['user', 'profile', 'fssai_no', 'active', 'properties', 'answers'] # , 'registration_time'
		case 'guests':
			model = Guest
			title = 'Guests'
			form = GuestForm
			headings = Guest.get_attributes()
		case 'listings':
			model = HostProperty
			title = 'Listings'
			headings = HostProperty.get_attributes()
		case 'host-profiles':
			model = HostProfile
			title = 'HostProfiles'
			headings = HostProfile.get_attributes()
		case 'guest-profiles':
			model = SonchiUserProfile
			title = 'Guests'
			form = SonchiUserProfile
			headings = SonchiUserProfile.get_attributes()
		case _:
			model = None


	if request.method == 'POST':
		try:
			print(dict(request.POST))
			obj = model.objects.get(id=request.POST.get('obj_id'))
			for heading in headings:
				try:
					value = request.POST.get(heading)
					setattr(obj, heading, value)
					obj.save()
				except:
					continue
			redirect(request.path)

		except:
			form = form(request.POST)
			if form.is_valid():
				obj = form.save()
				if title == 'Answers':
					obj.image_data = to_base64(request.FILES['image'])
					obj.save()
			
				redirect(request.path)

	ctx = {
		'title': title,
		'headings': headings,
		'form': form,
		'objects': objects if objects else (model.objects.all() if model else []),
	}

	return render(request, 'object_details.html', context=ctx)




def host_listing_data(request):
	session = Session.objects.get(session_key=request.GET.get('session_key'))
	lst = HostProperty.objects.get(id=request.GET.get('listing_id'))
	prf = HostProfile.objects.get(id=request.GET.get('profile_id'))
	
	if session :
		host = Host.objects.get(id=request.GET.get('host_id'))
		listing = list(filter( lambda a: a == lst, host.properties.all()))[0]
		profile = host.profile if prf == host.profile else HostProfile.objects.none()
		print('Listing', listing, profile)
		return JsonResponse({
			'id': host.id,
			# 'images': [img.image for img in listing.images.all()],
			'kitchenName': listing.kitchen_name,
			'verify': {
				'id': profile.identity_verified,
				'mobile':profile.mobile_verified,
				'email': profile.email_verified, 
			},
			'address': {
				'line': listing.address_line,
				'street': listing.address_street,
				'city': listing.address_city,
				'pincode': listing.address_pincode,
				'state': listing.address_state,
				'location': { 'lat': listing.address_lat, 'lng': listing.address_lng}
			},
			'hostName': f'{host.user.first_name} {host.user.last_name}',
			'bestOfBest': True,
			'about': {
				'aboutText': host.profile.about,
				'culturalInsights': {
					# 'img': ci.img,
					'description': listing.cultural_insights.description if listing.cultural_insights else '',
					'headings': listing.cultural_insights.headings.split('\n') if listing.cultural_insights else '',
					'detail_text': listing.cultural_insights.detail_text.split('\n') if listing.cultural_insights else '',
				},
				'socialMediaLinks': [
					host.profile.facebook,
					host.profile.instagram,
					host.profile.twitter,
					host.profile.youtube,
				]
			},
			'additional_info': {
				'house_rules': listing.additional_info.house_rules.detail_text.split('\n') if listing.additional_info else '',
				'security_safety': listing.additional_info.security_safety.detail_text.split('\n') if listing.additional_info else '',
				'cancelation_changes': listing.additional_info.cultural_insights.detail_text.split('\n') if listing.additional_info else '',
			},
			'ambiance': [{
				# 'img': ambi.image_data,
				'title': ambi.title,
				'description': ambi.description
			} for ambi in listing.ambiances.all()],

			'twd': list(filter(lambda a: a, [
				listing.twd.certificate if listing.twd else None, 
				listing.twd.coocking_aura if listing.twd else None, 
				listing.twd.test if listing.twd else None
			])),
			
			'amenities': [amen.title for amen in listing.amenities.all()],
			
			'guestRating': {
				'Food': 4.8,
				'Check-in': 4.5,
				'Cleanliness': 4.7,
				'Communication': 4.9,
				'Value': 4.6,
				'Accuracy': 4.8,
				'Location': 4.7
			},
			'guestReview': [{
				'image': rw.review_guest.profile.profile_img,
				'starRating': rw.star,
				'text': rw.review_text,
				'date': rw.date
			} for rw in Reviews.objects.filter(review_host=host)],
			'DateOfEvent': ['Mon', 'Tue', 'Wed'],
			'Timing': ['10am-12pm', '2pm-4pm'],
		})
	else:
		return HttpResponseNotAllowed()


def host_event_data(request):
	session = Session.objects.get(session_key=request.GET.get('session_key'))
	lst = HostProperty.objects.get(id=request.GET.get('listing_id'))
	prf = HostProfile.objects.get(id=request.GET.get('profile_id'))
	
	if session :
		host = Host.objects.get(id=request.GET.get('host_id'))
		listing = list(filter( lambda a: a == lst, host.properties.all()))[0]
		profile = host.profile if prf == host.profile else HostProfile.objects.none()
		print('Listing', listing, profile)
		return JsonResponse({
			'id': host.id,
			# 'images': [img.image for img in listing.images.all()],
			'kitchenName': listing.kitchen_name,
			'verify': {
				'id': profile.identity_verified,
				'mobile':profile.mobile_verified,
				'email': profile.email_verified, 
			},
			'address': {
				'line': listing.address_line,
				'street': listing.address_street,
				'city': listing.address_city,
				'pincode': listing.address_pincode,
				'state': listing.address_state,
				'location': { 'lat': listing.address_lat, 'lng': listing.address_lng}
			},
			'hostName': f'{host.user.first_name} {host.user.last_name}',
			'bestOfBest': True,
			'about': {
				'aboutText': host.profile.about,
				'culturalInsights': {
					# 'img': ci.img,
					'description': listing.cultural_insights.description if listing.cultural_insights else '',
					'headings': listing.cultural_insights.headings.split('\n') if listing.cultural_insights else '',
					'detail_text': listing.cultural_insights.detail_text.split('\n') if listing.cultural_insights else '',
				},
				'socialMediaLinks': [
					host.profile.facebook,
					host.profile.instagram,
					host.profile.twitter,
					host.profile.youtube,
				]
			},
			'additional_info': {
				'house_rules': listing.additional_info.house_rules.detail_text.split('\n'),
				'security_safety': listing.additional_info.security_safety.detail_text.split('\n'),
				'cancelation_changes': listing.additional_info.cultural_insights.detail_text.split('\n')
			},
			'ambiance': [{
				# 'img': ambi.image_data,
				'title': ambi.title,
				'description': ambi.description
			} for ambi in listing.ambiances.all()],

			'twd': [listing.twd.certificate, listing.twd.coocking_aura, listing.twd.test],
			
			'amenities': [amen.title for amen in listing.amenities.all()],
			
			'guestRating': {
				'Food': 4.8,
				'Check-in': 4.5,
				'Cleanliness': 4.7,
				'Communication': 4.9,
				'Value': 4.6,
				'Accuracy': 4.8,
				'Location': 4.7
			},
			'guestReview': [{
				'image': rw.review_guest.profile.profile_img,
				'starRating': rw.star,
				'text': rw.review_text,
				'date': rw.date
			} for rw in Reviews.objects.filter(review_host=host)],
			'DateOfEvent': ['Mon', 'Tue', 'Wed'],
			'Timing': ['10am-12pm', '2pm-4pm'],
		})
	else:
		return HttpResponseNotAllowed()


def add_property(request):
	if request.method == 'POST':
		h_prop = HostProperty(
			property_host = Host.objects.get(id=request.POST.get('host_id')),
			about = request.POST.get('about'),
			location = request.POST.get('location'),
			open_status = True
		)
		return JsonResponse(HostProperty.json())

@csrf_exempt
def book_event(request):
	if request.method == 'POST':
		event = EventBooking(
			location = HostProperty.objects.filter(id=request.POST.get('property_id'))[0],
			event_guest = Guest.objects.filter(id=request.POST.get('guest_id'))[0],
			status = 'BOOKED',
			no_people = request.POST.get('number_people'),
			time = request.POST.get('event_time')
		)
		event.save()
		return JsonResponse({'event_id': event.id, 'status': event.status, 'paid': event.paid})
	else:
		return HttpResponseNotAllowed()

def home_search_handle(request):
	return [] # search Results

def services(request):
	return JsonResponse({
		'services': [ourservice.to_json() for ourservice in OurServices.objects.all()]
	})

def reviews(request):
	return JsonResponse({
		'reviews': [r.to_json() for r in Reviews.objects.all()[48:]]
	})

def home_host_lists(request):
 	return JsonResponse({
 			'hosts': [h.to_json() for h in Hosts.objects.all()[48:]]
 	});


def hosts(request):
 	return JsonResponse({
 		'hosts': [h.to_json() for h in Hosts.objects.all()[48:]]
 	})


def blogs(request):
 	return JsonResponse({
 		'blogs': [r.to_json() for r in Reviews.objects.all()[48:]]
 	})






# if len(lst_amb) > 3:
# 	for amb in lst_amb[3:]:
# 		obj = Ambiance.objects.get(id=amb.id)
# 		obj.delete()
# for i, a in enumerate(host_inputs.get('ambiances')[:3]):
# 	try:
# 		obj = Ambiance.objects.get(id=lst_amb[i].id)
# 		obj.title = a[0]
# 		obj.description = a[1]
# 		obj.amb_type = amb_types[i]
# 		obj.save()
# 	except:
# 		obj = Ambiance(amb_type=amb_types[i], title=a[0], description=a[1])
# 		obj.save()
# 		listing.ambiances.add(obj)
# 		listing.save()