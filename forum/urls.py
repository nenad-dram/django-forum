from django.urls import path

from forum import views
from forum.views import LoginUser

urlpatterns = [
    path('home', views.dashboard, name='home'),
    path('login', LoginUser.as_view(), name='login'),
    path('logout', views.logout_user, name='logout'),
    path('<str:name>', views.subcategory, name='subcategory'),
    path('<str:subcategory_name>/createthread', views.thread_create, name='thread_create'),
    path('thread/<int:id>', views.thread_view, name='thread_view'),
    path('thread/<int:root_id>/reply', views.thread_reply, name='thread_reply'),
    path('thread/<int:thread_id>/getupdated', views.thread_get_updated_date, name='thread_get_update'),
    path('thread/<int:thread_id>/editmessage', views.thread_edit_message, name='thread_edit_message'),
]
