from accounts.views import signup, profile_nl, login_user_nl, logout_user_nl, signup_nl, delete_account, \
    delete_account_nl
from accounts.views import logout_user, login_user, profile, set_default_shipping_address, delete_address
from django.urls import path



urlpatterns = [
    path('signup/', signup, name="signup"),
    path('nl/signup/', signup_nl, name='signup-nl'),
    path('delete_address/<int:pk>', delete_address, name="delete_address"),
    path('delete_account/', delete_account, name="delete-account"),
    path('nl/delete_account/', delete_account_nl, name='delete-account-nl'),
    path('login/', login_user, name="login"),
    path('logout/', logout_user, name="logout"),
    path('nl/login/', login_user_nl, name='login-nl'),
    path('nl/logout/', logout_user_nl, name='logout-nl'),
    path('profile/', profile, name="profile"),
    path('profile/set_defaut_shipping/<int:pk>/', set_default_shipping_address, name="set-default-shipping"),
    path('nl/account/profile/', profile_nl, name='profile-nl'),

]