from django.http import HttpResponse
from django.http import HttpResponseRedirect
import datetime
import redis
import uuid
import math
import time
from uuid import uuid4
from django.template import Template, Context
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import Http404

conn = redis.Redis()


def htmlRender(html_name):
    fp = open(html_name)
    t = Template(fp.read())
    fp.close()
    html = t.render(Context())
    return HttpResponse(html)


def open_html(html_name):
    fp = open(html_name)
    t = Template(fp.read())
    fp.close()
    return t


def first_page(request):
    html = htmlRender('template/firstPage.html')
    return HttpResponse(html)


def signin_form(request):
    fp = open('template/signIn.html')
    t = Template(fp.read())
    fp.close()
    html = t.render(Context())
    return HttpResponse(html)
    #return render_to_response('C:\\Users\\Fatemeh\\Desktop\\nosql\\project1\\django\\mysite\\search_form.html')

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        id = create_user(request.POST['name'],request.POST['userName'],request.POST['pass'])
        if id is None:
            t = open_html('template/signUp.html')
            html = t.render(Context({'message': 'User existing before!!'}))
        else:
            pipeline = conn.pipeline(True)
            pipeline.hget('user:%s' % id, 'pass')
            pipeline.hget('user:%s' % id, 'login')
            pipeline.hget('user:%s' % id, 'name')
            dbpass, dbusername, dbname = pipeline.execute();
            html = 'id is %d ' % id + dbname + " " + dbusername + " " + dbpass # just for test
            t = open_html('template/firstPage.html')
            html += t.render(Context({'message': 'Your account correctly added, for enter please sign in.'}))

    else:
        html = htmlRender('template/signUp.html')
    return HttpResponse(html)


@csrf_exempt
def signin(request):
    if request.method == 'POST':
        find = find_user(request.POST['userName'],request.POST['pass'])
        if find != False:
            request.session['member_id'] = find
            return HttpResponseRedirect('/home/')
        else:
            t = open_html('template/signIn.html')
            message = HttpResponse(t.render(Context({'message': 'user name or pass is not correct!!'})))
    else:
        message = htmlRender('template/signIn.html')
    return message


def date(request):
    now = datetime.datetime.now();
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


#def home(request):
    #if request.session.get is None: #shoud be checked if session not defind
#    if "member_id" not in request.session:
#        return HttpResponseRedirect('/signin/')
#    id = request.session.get('member_id')
#    t = open_html('template/home.html')
#    html = t.render(Context({'name': get_user_name(id), 'username': get_user_loginname(id)}))
#    return HttpResponse(html)


def home(request):
    #if request.session.get is None: #shoud be checked if session not defind
    if "member_id" not in request.session:
        return HttpResponseRedirect('/signin/')
    id = request.session.get('member_id')
    prof = get_status_messages2(conn, id, timeline='profile:', page=1, count=30)
    fp = open('template/home.html')
    t = Template(fp.read())
    fp.close()
    html = t.render(Context({'name': get_user_name(id), 'username': get_user_loginname(id) , 'item_list': prof,}))
    return HttpResponse(html)


def init(request):
    conn.set('user:id:', 0)
    return HttpResponse()


def dateCal(request, index):
    try:
        index = int(index)
    except ValueError:
        raise Http404()
    dt = datetime.datetime.now() + datetime.timedelta(hours=index)
    out = conn.get('this')
    html = "<html><body>In %s hour(s), it will be %s database value: %s.</body></html>" % (index, dt,out)
    return HttpResponse(html)


def current_datetime(request):
    id = request.session.get('member_id')
    user = get_user_all(id)
    now = datetime.datetime.now()
    fp = open('template/t1.html')
    t = Template(fp.read())
    fp.close()
    html = t.render(Context({'item_list': user.iteritems(),'ship_date': now}))
    return HttpResponse(html)


@csrf_exempt
def change_info(request):
    if request.method == 'POST':
        #new info submited
        id = request.session.get('member_id')
        name = get_user_name(id)

        publicChoice = request.POST.get('publicity',0)

        change_user_info(id, request.POST['name'],request.POST['pass'],publicChoice)
        user = get_user_all(id)
        now = datetime.datetime.now()
        fp = open('template/t1.html')
        t = Template(fp.read())
        fp.close()
        html = t.render(Context({'item_list': user.iteritems()}))
        return HttpResponseRedirect('/home/')
    else:
        id = request.session.get('member_id')
        name = get_user_name(id)
        t = open_html('template/changeInfo.html')
        html = t.render(Context({'name':'value=%s' % name}))
    return HttpResponse(html)


@csrf_exempt
def search_result(request):
    if request.method == 'POST':
        user_name = request.POST['username']
        t = open_html('template/foundUser.html')
        found_id = find_user_by_username(user_name)
        if found_id is None:
            html = t.render(Context({'class1': 'class=behide'}))
        else:
            found_name = get_user_name(found_id)
            found_username = get_user_loginname(found_id)
            id = request.session.get('member_id')
            if is_blocked(id,found_id):
                #unblock
                html = t.render(Context({'class2': 'class=behide', 'name': found_name, 'username': found_username,
                                         'followBtn': 'class=behide', 'foundId': 'value=%s' % found_id ,
                                        'BlockedBtn': 'class=behide','unFollowBtn': 'class=behide',
                                         'isBlocked': 'class=behide','isPrivate':'class=behide',
                                         'showInfoPageBtn': 'class=behide'}))
            elif is_blocked(found_id , id):
                #you are blocked
                html = t.render(Context({'class2': 'class=behide', 'name': found_name, 'username': found_username,
                                         'followBtn': 'class=behide', 'foundId': 'value=%s' % found_id,
                                         'unBlockedBtn': 'class=behide', 'unFollowBtn': 'class=behide' ,
                                         'isPrivate':'class=behide','showInfoPageBtn': 'class=behide'}))
            elif is_followed(id,found_id): #followed before
                html = t.render(Context({'class2': 'class=behide' , 'name':found_name , 'username':found_username,
                                         'followBtn':'class=behide', 'foundId':'value=%s'%found_id,
                                         'isBlocked': 'class=behide','unBlockedBtn': 'class=behide',
                                         'isPrivate':'class=behide'}))
            elif is_private(found_id):
                html = t.render(Context({'class2': 'class=behide', 'name': found_name, 'username': found_username,
                                         'unFollowBtn': 'class=behide', 'foundId': 'value=%s' % found_id,
                                         'isBlocked': 'class=behide', 'unBlockedBtn': 'class=behide',
                                         'showInfoPageBtn': 'class=behide'}))
            else:
                html = t.render(Context({'class2': 'class=behide', 'name': found_name, 'username': found_username,
                                         'unFollowBtn': 'class=behide', 'foundId':'value=%s'%found_id,
                                         'isBlocked': 'class=behide','unBlockedBtn': 'class=behide',
                                         'isPrivate':'class=behide'}))
        out = HttpResponse(html)
    else:
        raise Http404()
    return HttpResponse(out)


@csrf_exempt
def follow(request):
    if request.method == 'POST':
        foundId = request.POST['foundId']
        id = request.session.get('member_id')
        if follow_user(id,foundId) is None:
            return HttpResponse('error happens')
    return HttpResponseRedirect('/home/')



@csrf_exempt
def unfollow(request):
    if request.method == 'POST':
        foundId = request.POST['foundId']
        id = request.session.get('member_id')
        if unfollow_user(id,foundId) is None:
            return HttpResponse('error happens')
    return HttpResponseRedirect('/home/')


def logout(request):
    try:
        del request.session['member_id']
    except KeyError:
        return HttpResponse('error happens')
    return HttpResponseRedirect('/twitter/')

def show_followings(request):
    id = request.session.get('member_id')
    id_list = following_list(id)
    list = makeUserList(id_list)
    t = open_html('template/followList.html')
    html = t.render(Context({'header': 'List of followings', 'item_list': list,'func':'show_followings'}))
    return HttpResponse(html)

def show_followers(request):
    id = request.session.get('member_id')
    id_list = follower_list(id)
    list = makeUserList(id_list)
    t = open_html('template/followList.html')
    html = t.render(Context({'header': 'List of followers', 'item_list':list, 'func':'show_followers'}))
    return HttpResponse(html)



@csrf_exempt
def block(request):
    if request.method == 'POST':
        foundId = request.POST['foundId']
        id = request.session.get('member_id')
        if make_block_user(id, foundId) is False:
            return HttpResponse('error happens')
    return HttpResponseRedirect('/home/')

@csrf_exempt
def unblock(request):
    if request.method == 'POST':
        foundId = request.POST['foundId']
        id = request.session.get('member_id')
        if make_unblock_user(id, foundId) is False:
            return HttpResponse('error happens')
    return HttpResponseRedirect('/home/')




#########################################################################################################


def release_lock(conn, lockname, identifier):
    pipe = conn.pipeline(True)
    lockname = 'lock:' + lockname
    while True:
        try:
            pipe.watch(lockname)
            if pipe.get(lockname) == identifier:
                pipe.multi()
                pipe.delete(lockname)
                pipe.execute()
                return True
            pipe.unwatch()
            break
        except redis.exceptions.WatchError:
            pass
    return False


def acquire_lock_with_timeout(conn, lockname, acquire_timeout=10, lock_timeout=10):
    identifier = str(uuid.uuid4())
    lockname = 'lock:' + lockname
    lock_timeout = int(math.ceil(lock_timeout))
    end = time.time() + acquire_timeout
    while time.time() < end:
        if conn.setnx(lockname, identifier):
            conn.expire(lockname, lock_timeout)
            return identifier
        elif not conn.ttl(lockname):
            conn.expire(lockname, lock_timeout)
        time.sleep(.001)
    return False


def create_user(name, login, password):
    llogin = login.lower()
    lock = acquire_lock_with_timeout(conn, 'user:' + llogin, 1)
    if not lock:
        return None
    if conn.hget('users:', llogin):
        return None
    id = conn.incr('user:id:')
    pipeline = conn.pipeline(True)
    pipeline.hset('users:', llogin, id)
    pipeline.hmset('user:%s'%id, {
        'login': login,
        'id': id,
        'name': name,
        'pass': password,
        'followers': 0,
        'following': 0,
        'posts': 0,
        'signup': time.time(),
        'isPrivate':0,
    })
    pipeline.execute()
    release_lock(conn, 'user:' + llogin, lock)
    return id


def find_user(login , password):
    llogin = login.lower()
    userId = conn.hget('users:', llogin)
    if userId is None:
        return False
    else:
        dataBasePass = conn.hget('user:%s'%userId,'pass')
        if dataBasePass == password:
            return userId
        else:
            return False


def change_user_info(userId , name, password,publicity):
    pipeline = conn.pipeline(True)
    pipeline.hset('user:%s' % userId, 'pass', password)
    pipeline.hset('user:%s' % userId, 'name', name)
    pipeline.hset('user:%s' % userId, 'isPrivate', publicity)
    pipeline.execute()


def get_user_loginname(userId):
    name = conn.hget('user:%s' % userId, 'login')
    return name

def get_user_name(userId):
    name = conn.hget('user:%s' % userId, 'name')
    return name


def get_post_content(postId):
    msg = conn.hget('status:%s' % postId, 'message')
    return msg


def get_user_all(userId):
    user = conn.hgetall('user:%s' % userId)
    #for key, value in user.iteritems():
    #    output[key.decode(self.encoding)] = value.decode(self.encoding)
    return user


def find_user_by_username(user_name):
    id = conn.hget('users:',user_name)
    return id

HOME_TIMELINE_SIZE = 1000
def follow_user(uid, other_uid):
    HOME_TIMELINE_SIZE = 1000
    fkey1 = 'following:%s'%uid
    fkey2 = 'followers:%s'%other_uid
    if conn.zscore(fkey1, other_uid):
        return None
    now = time.time()
    pipeline = conn.pipeline(True)
    pipeline.zadd(fkey1, other_uid, now)
    pipeline.zadd(fkey2, uid, now)
    pipeline.zcard(fkey1)
    pipeline.zcard(fkey2)
    pipeline.zrevrange('profile:%s' % other_uid, 0, HOME_TIMELINE_SIZE - 1, withscores=True)
    following, followers, status_and_score = pipeline.execute()[-3:]
    pipeline.hset('user:%s' % uid, 'following', following)
    pipeline.hset('user:%s' % other_uid, 'followers', followers)
    #home , time line
    if status_and_score:
        pipeline.zadd('home:%s' % uid, **dict(status_and_score))
    pipeline.zremrangebyrank('home:%s' % uid, 0, -HOME_TIMELINE_SIZE - 1)
    pipeline.execute()
    return True


def unfollow_user(uid, other_uid):
    HOME_TIMELINE_SIZE = 1000
    fkey1 = 'following:%s'%uid
    fkey2 = 'followers:%s'%other_uid
    if not conn.zscore(fkey1, other_uid):
        return None
    pipeline = conn.pipeline(True)
    pipeline.zrem(fkey1, other_uid)
    pipeline.zrem(fkey2, uid)
    pipeline.zcard(fkey1)
    pipeline.zcard(fkey2)
    pipeline.zrevrange('profile:%s'%other_uid,0, HOME_TIMELINE_SIZE-1)
    following, followers, statuses = pipeline.execute()[-3:]
    pipeline.hset('user:%s'%uid, 'following', following)
    pipeline.hset('user:%s'%other_uid, 'followers', followers)
    if statuses:
        pipeline.zrem('home:%s'%uid, *statuses)
    pipeline.execute()
    return True


def is_followed(uid, other_uid):
    fkey1 = 'following:%s' % uid
    if conn.zscore(fkey1, other_uid):
        return True
    return False


def follower_list(uid):
    list = conn.zrevrange('followers:%s'%uid, 0, -1)
    return list


def following_list(uid):
    list = conn.zrevrange('following:%s' % uid, 0, -1)
    return list


def makeUserList(input_list):
    i = 0
    output_list=input_list
    for item in input_list:
        #user_name = get_user_loginname(item)
        user = conn.hgetall('user:%s'%item)
        output_list[i] = user
        i = i+1

    return output_list


def make_block_user(uid,other_uid):
    now = time.time()
    unfollow_user(uid,other_uid)
    unfollow_user(other_uid,uid)
    pipeline = conn.pipeline(True)
    pipeline.zrem('block:%s' % uid, other_uid)
    pipeline.zadd('block:%s' % uid, other_uid,now)
    pipeline.execute()
    return True


def make_unblock_user(uid,other_uid):
    pipeline = conn.pipeline(True)
    pipeline.zrem('block:%s' % uid,other_uid)
    pipeline.execute()
    return True


def is_blocked(uid, other_uid):
    fkey1 = 'block:%s' % uid
    if conn.zscore(fkey1, other_uid):
        return True
    return False


def is_private(uid):
    fkey1 = 'user:%s' % uid
    isPriv=conn.hget(fkey1, 'isPrivate')
    if isPriv:
        return True
    return False


################################sarah part###########################################

#Sarah comming
@csrf_exempt
def newTweet(request):
    # out= 'me before you'
    if request.method == 'POST':
         tweet=request.POST['tweet']
         id=request.session.get('member_id')
         if tweet!=None :
             post_status(conn, id, tweet)
         out = 'your message  ' + tweet + ' was sent'
         return HttpResponseRedirect('/home/')
    # out = 'hello '
    else:
        out = htmlRender('template/newTweet.html')
    return HttpResponse(out)


@csrf_exempt
def changeTweet(request):
    if request.method == 'POST':
        id = request.session.get('member_id')
        tweetId= request.POST['tweetId']
        post = conn.hget('status:%s' % tweetId,'message')
        t=open_html('template/changeTweet.html')
        html = t.render(Context({'tweet': post,'tweetId': tweetId}))
        out=HttpResponse(html)
    else:
        raise Http404()
    return HttpResponse(out)

@csrf_exempt
def changeMessage(request):
    if request.method == 'POST':
        newTweet = request.POST['newTweet']
        tweetId= request.POST['tweetId']
        # post = conn.hgetall('status:%s' % tweetId)
        pipeline = conn.pipeline(True)
        pipeline.hset('status:%s' % tweetId, 'message', newTweet)
        pipeline.execute()
        post = conn.hget('status:%s' % tweetId, 'message')
        id=conn.hget('status:%s' % tweetId, 'id')
        # out = 'your message  #' +id +'\t'+ post + ', was edited. '

        #out = 'your message  ' +  post + ' was sent'
    else:
        raise Http404()
    return HttpResponseRedirect('/home/')


@csrf_exempt
#delete all comments
def deleteTweet(request):
    if request.method == 'POST':
        tweetId= request.POST['tweetId']
        id = request.session.get('member_id')
        post = conn.hget('status:%s' % tweetId, 'message')
        delete_status(conn, id, tweetId)
        # post = conn.hgetall('status:%s' % tweetId)

        # out = 'your message  #' +id +'\t'+ post + ', was edited. '

        out = 'your message  ' +  post + ' was sent'
    else:
        raise Http404()
    return HttpResponseRedirect('/home/')


def timeLine(request):
    id = request.session.get('member_id')
    prof = get_status_messages2(conn, id, timeline='home:', page=1, count=30)
    fp = open('template/timeLine.html')
    t = Template(fp.read())
    fp.close()
    html = t.render(Context({'item_list': prof}))
    return HttpResponse(html)

@csrf_exempt
def show_info_page(request):
    if request.method == 'POST':
        foundId = request.POST['foundId']
        foundUserName = get_user_loginname(foundId)
        foundName = get_user_name(foundId)
        prof = get_status_messages2(conn, foundId, timeline='profile:', page=1, count=30)
        fp = open('template/info.html')
        t = Template(fp.read())
        fp.close()
        html = t.render(Context({'name': foundName,'userName': foundUserName,'item_list': prof}))
        return HttpResponse(html)

@csrf_exempt
def comment(request):
    if request.method == 'POST':
        thisfoundId = request.POST.get('foundId',None)
        thisPostId = request.POST.get('postId',None)
        msg = get_post_content(thisPostId)
        t = open_html('template/showComment.html')
        username = get_user_loginname(thisfoundId)
        cmnt = get_status_messages_comment(conn, thisPostId, timeline='commentCollection:', page=1, count=30)
        html = t.render(Context({'userName': username, 'status': msg, 'item_list': cmnt , 'postId': thisPostId,
                                 'findId':thisfoundId}))
        return HttpResponse(html)
    else:
        raise Http404()


@csrf_exempt
def commentAjax(request):
    if request.method == 'POST':
        thisfoundId = request.POST.get('foundId',None)
        thisPostId = request.POST.get('postId',None)
        msg = get_post_content(thisPostId)
        t = open_html('template/commentList.html')
        username = get_user_loginname(thisfoundId)
        cmnt = get_status_messages_comment(conn, thisPostId, timeline='commentCollection:', page=1, count=30)
        html = t.render(Context({'userName': username, 'item_list': cmnt , 'postId': thisPostId,
                                 'findId':thisfoundId}))
        return HttpResponse(html)
    else:
        raise Http404()

@csrf_exempt
def sendComment(request):
    #send comment
    if request.method == 'POST':
        uid = request.session.get('member_id')
        pid = request.POST['postId']
        thisfindId = request.POST['findId']
        message = request.POST['msgContent']
        x=post_comment(conn, uid, message,pid)
        t=open_html('template/temp.html')
        html=t.render(Context({'postId':pid,'foundId':thisfindId}))
        return HttpResponse(html)


##################################################################3
#Sarah comming!
def create_status(conn, uid, message, **data):
    pipeline = conn.pipeline(True)
    pipeline.hget('user:%s'%uid, 'login')
    pipeline.incr('status:id:')
    login, id = pipeline.execute()
    if not login:
        return None
    data.update({
        'message': message,
        'posted': time.time(),
        'id': id,
        'uid': uid,
        'login': login,
    })
    pipeline.hmset('status:%s'%id, data)
    pipeline.hincrby('user:%s'%uid, 'posts')
    pipeline.execute()
    return id

def post_status(conn, uid, message, **data):
    id = create_status(conn, uid, message, **data)
    if not id:
        return None
    posted = conn.hget('status:%s'%id, 'posted')
    if not posted:
        return None
    post = {str(id): float(posted)}
    conn.zadd('profile:%s'%uid, **post)
    syndicate_status(conn, uid, post)
    return id


POSTS_PER_PASS = 1000
def syndicate_status(conn, uid, post, start=0):
    followers = conn.zrangebyscore('followers:%s' % uid, start, 'inf', start=0, num=POSTS_PER_PASS, withscores=True)
    pipeline = conn.pipeline(False)
    for follower, start in followers:
        pipeline.zadd('home:%s' % follower, **post)
        pipeline.zremrangebyrank('home:%s' % follower, 0, -HOME_TIMELINE_SIZE - 1)
        pipeline.execute()
    if len(followers) >= POSTS_PER_PASS:
        execute_later(conn, 'default', 'syndicate_status', [conn, uid, post, start])


def get_status_messages(conn, uid, timeline='home:', page=1, count=30):
    statuses = conn.zrevrange('%s%s'%(timeline, uid), (page-1)*count, page*count-1)
    pipeline = conn.pipeline(True)
    for id in statuses:
        pipeline.hgetall('status:%s'%id)
    return filter(None, pipeline.execute())


def get_status_messages2(conn, uid, timeline='profile:', page=1, count=30):
    statuses = conn.zrevrange('%s%s'%(timeline, uid), (page-1)*count, page*count-1)
    pipeline = conn.pipeline(True)
    for id in statuses:
        pipeline.hgetall('status:%s'%id)
    return filter(None, pipeline.execute())



def delete_status(conn, uid, status_id):
    key = 'status:%s'%status_id
    lock = acquire_lock_with_timeout(conn, key, 1)
    if not lock:
        return None
    if conn.hget(key, 'uid') != str(uid):
        return None
    pipeline = conn.pipeline(True)
    pipeline.delete(key)
    pipeline.zrem('profile:%s'%uid, status_id)
    pipeline.zrem('home:%s' % uid, status_id)
    pipeline.hincrby('user:%s' % uid, 'posts', -1)
    pipeline.execute()
    release_lock(conn, key, lock)
    return True


def create_comment(conn, uid, message, pid, **data):
    pipeline = conn.pipeline(True)
    pipeline.hget('user:%s'%uid, 'login')
    pipeline.incr('comment:id:') #attention
    login, id = pipeline.execute()
    if not login:
        return None
    data.update({
        'message': message,
        'posted': time.time(),
        'id': id,
        'uid': uid,
        'login': login,
        'pid' : pid
    })
    pipeline.hmset('comment:%s'%id, data)
    #pipeline.hincrby('user:%s'%uid, 'posts')
    pipeline.execute()
    return id

def post_comment(conn, uid, message,pid, **data):
    id = create_comment(conn, uid, message,pid, **data)
    if not id:
        return None
    posted = conn.hget('comment:%s'%id, 'posted')
    if not posted:
        return False
    post = {str(id): float(posted)}
    conn.zadd('commentCollection:%s'%pid, **post)
    #syndicate_status(conn, uid, post)
    return id

def get_status_messages_comment(conn, pid, timeline='commentCollection:', page=1, count=30):
    statuses = conn.zrevrange('%s%s'%(timeline, pid), (page-1)*count, page*count-1)
    pipeline = conn.pipeline(True)
    for id in statuses:
        pipeline.hgetall('comment:%s'%id)
    return filter(None, pipeline.execute())