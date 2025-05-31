from django.urls import path, include

from .views import login_user, logout_user, signup, verify_session, book_event, add_property
from .views import check_login_status, update_profile_data, host_onboard, host_update, host_listing_data, host_event_data
from .views import admin_dashboard, admin_users


app_name = 'user_manage'

urlpatterns = [
	path('login', login_user, name="login"),
	path('signup', signup, name="signup"),
	path('logout-user', logout_user, name="logout"),
	path('update_profile', update_profile_data, name='update-profile'),
	path('verify-session', verify_session, name="verify-session"),
	path('host-onboard', host_onboard, name="host-onboard"),
	path('host-listing-data', host_listing_data, name="host-listing-data"),
	path('host-event-data', host_event_data, name="host-event-data"),
	path('host-update', host_update, name="host-update"),
	path('add-property', add_property, name="add_property"),
	path('book-event', book_event, name="book-event"),
	path('check-session', check_login_status, name="book-event"),





	# path('admin-dashboard', admin_dashboard, name="admin-dashboard"),
	# path('admin-dashboard/users', admin_users, name="admin-users"),

	path('admin-dashboard/', include([
		path('', admin_dashboard, name="admin-dashboard"),
		# path('/', admin_dashboard, name="admin-dash"),
		path('users', admin_users, name="admin-users"),
		path('guests', admin_users, name="admin-guests"),
		path('hosts', admin_users, name="admin-hosts"),
		path('listings', admin_users, name="admin-listings"),
		path('questions', admin_users, name="admin-questions"),
		path('answers', admin_users, name="admin-answers"),
		path('host-profiles', admin_users, name="host-profiles"),
		path('guest-profiles', admin_users, name="guest-profiles"),
	]))
]