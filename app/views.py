from facebook import get_user_from_cookie, GraphAPI
from functools import wraps
from flask import g, jsonify, render_template, redirect, request, session, url_for
from app import app
from babbler import get_reply

# Facebook app details
FB_APP_ID = '1561303244188583'
FB_APP_NAME = 'Kawaii Tomodachi-desu'
FB_APP_SECRET = '51026d49c3cf27a091d502b1f8ef0698'

# Max number of objects to return from FB query
REQUEST_LIMIT = 100

# Login wrapper
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    user = session.get('user')
    return render_template('index.html', app_id=FB_APP_ID,
                           app_name=FB_APP_NAME, user=user,
                           root_url=request.url_root)


@app.route('/login')
def login():
    """Log in user on Facebook."""
    next = request.args.get('next') or url_for('index')
    return render_template('login.html', app_id=FB_APP_ID, name=FB_APP_NAME,
                           next=next)

@app.route('/logout')
def logout():
    """Log out the user from the application.

    Log out the user from the application by removing them from the
    session.  Note: this does not log the user out of Facebook - this is done
    by the JavaScript SDK.
    """
    session.pop('user', None)
    g.user = None
    return redirect(url_for('index'))


@app.route('/date/<friendId>', methods=['GET'])
@login_required
def date_friend(friendId=None):
    """ Return a json of a random friend's data."""
    user = session.get('user')
    access_token = session.get('access_token', None)

    try:
        graph = GraphAPI(access_token)
    except GraphAPIError as e:
        # If something went wrong with token, redirect to login
        return redirect(url_for('login'))

    graph = GraphAPI(access_token)
    profile = graph.get_object(friendId)
    friend = profileToDict(profile)

    session['friend'] = friendId
    # TODO: render actual dating page
    return render_template('dating.html', app_id=FB_APP_ID,
                           app_name=FB_APP_NAME, user=user,
                           friend=friend)


@app.route('/babble', methods=['GET'])
@login_required
def gen_babble():
    access_token = session.get('access_token', None)
    if not access_token:
        return jsonify(dialogue=None)

    try:
        graph = GraphAPI(access_token)
    except GraphAPIError as e:
        return jsonify(dialogue=None, error=e)

    friendId = session['friend']
    posts = graph.get_connections(id=friendId, connection_name='posts', limit=REQUEST_LIMIT)

    dialogue = babble_posts(posts)
    # TODO: generate responses for you
    return jsonify(them=dialogue, you=['Hello', 'Hi', 'Hey', 'Yo'])

@app.route('/friends', methods=['GET'])
@login_required
def get_friends():
    access_token = session.get('access_token', None)
    if not access_token:
        return jsonify(friends=None)

    try:
        graph = GraphAPI(access_token)
    except GraphAPIError as e:
        return jsonify(friends=None, error=e)

    friends = graph.get_connections(id='me', connection_name='friends')
    if not friends.data:
        # you have no friends :(
        return jsonify(friends=None)

    return jsonify(friends=friends.data)


def babble_posts(posts):
    if not posts['data']:
        return ''
    return get_reply([post.get('message') for post in posts['data'] if post.get('message')])


@app.before_request
def get_current_user():
    """Set g.user to the currently logged in user.

    Called before each request, get_current_user sets the global g.user
    variable to the currently logged in user.  A currently logged in user is
    determined by seeing if it exists in Flask's session dictionary.

    If it is the first time the user is logging into this application it will
    create the user.  If the user is not logged in, None will be set to g.user.
    """

    # Set the user in the session dictionary as a global g.user and bail out
    # of this function early.
    if session.get('user'):
        g.user = session.get('user')
        return

    # Attempt to get the short term access token for the current user.
    result = get_user_from_cookie(cookies=request.cookies, app_id=FB_APP_ID,
                                  app_secret=FB_APP_SECRET)

    # If there is no result, we assume the user is not logged in.
    if result:
        # Not an existing user so get info
        try:
            graph = GraphAPI(result['access_token'])
        except GraphAPIError:
            return
        profile = graph.get_object('me')

        # Add the user to the current session
        session['user'] = profileToDict(profile)
        session['access_token'] = result['access_token']

    # Set the user as a global g.user
    g.user = session.get('user', None)

def profileToDict(profile):
    if 'link' not in profile:
        profile['link'] = ""
    return dict(name=profile['name'],
                profile_url=profile['link'],
                id=str(profile['id']))
