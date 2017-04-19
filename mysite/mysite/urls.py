"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from mysite.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^home/$', home),
    url(r'^date/$', date),
    url(r'^date/(\d{1,2})/$', dateCal),
    url(r'^temDate/$', current_datetime),

    #url(r'^signup_form/$', signUp_form),
    url(r'^signup/$',signup),
    url(r'^signin/$',signin),
    #url(r'^signin_form/$',signin_form),
    url(r'^init/$',init),
    url(r'^change_info/$',change_info),
    url(r'^search/$', search_result),
    url(r'^twitter/$', first_page),
    url(r'^follow/$', follow),
    url(r'^unfollow/$', unfollow),
    url(r'^logout/$', logout),
    url(r'^show_followings/$', show_followings),
    url(r'^show_followers/$', show_followers),
    url(r'^newTweet/$',newTweet),
    url(r'^block/$',block),
    url(r'^unblock/$',unblock),
    url(r'^changeTweet/$',changeTweet),
    url(r'^changeMessage/$',changeMessage),
    url(r'^deleteTweet/$',deleteTweet),
    url(r'^timeLine/$', timeLine),
    url(r'^show_info_page/$', show_info_page),

    url(r'^comment/$', comment),
    url(r'^sendComment/$', sendComment),
    url(r'^commentAjax/$', commentAjax),
]
