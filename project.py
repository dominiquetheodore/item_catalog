from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User, SubCategory
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import os
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask import make_response
import requests

# folder to upload product and subcategory pictures
UPLOAD_FOLDER = 'static/products/'
SUBCAT_FOLDER = 'static/subcategories/'

# allowed file extensions for images
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SUBCAT_FOLDER'] = SUBCAT_FOLDER


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Classified App"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def allowed_file(filename):
    """ returns true if file type is allowed for upload """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def createUser(login_session):
    """ create a new user ready to be registered """
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """ retrieve user record from ID """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """ get user record from email """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None


@app.route('/get_subcats', methods=['POST'])
def get_subcats():
    """ retrieve all subcategories """
    cat_id = request.form.get('category')
    subcats = session.query(SubCategory).filter_by(cat_id=cat_id)
    subs = dict()
    for subcat in subcats:
        subs[subcat.id] = subcat.name
    print subs
    return json.dumps({'resp': subs})


@app.route('/login')
def showLogin():
    """ display login page with anti-forgery state token """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # OAuth Login/Logout functions from Full Stack Foundations Course
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        username = login_session['email']
        error_msg = 'Current user is already connected.'
        response = make_response(json.dumps(error_msg), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # create new user if not registered
    if getUserID(login_session['email']):
        login_session['user_id'] = getUserID(login_session['email'])
    else:
        login_session['user_id'] = createUser(login_session)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """ DISCONNECT - Revoke a current user's token and reset 
    their login_session """
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return redirect('/')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON Endpoints
@app.route('/shop/<int:category_id>/<int:subcategory_id>/JSON')
def subcategoryJSON(category_id, subcategory_id):
    """ retrieve all items in a subcategory """
    items = session.query(Item).filter_by(subcat_id=subcategory_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/shop/<int:product_id>/JSON')
def itemJSON(product_id):
    """retrieve a product by ID """
    item = session.query(Item).filter_by(id=product_id).one()
    return jsonify(Item=[item.serialize])


@app.route('/shop/categories/JSON')
def categoriesJSON():
    """retrieve all categories """
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/shop/new/', methods=['GET', 'POST'])
def newItem():
    """ create a new product/ad: with or without image """
    if 'username' not in login_session:
        # check if the current user is logged in
        return redirect('/login')

    if request.method == 'POST':
        # form has been submitted
        file = None
        cat_id = None
        subcat_id = None
        name = None
        description = None

        if request.form['category']:
            cat_id = request.form['category']
        if request.form['subcategory']:
            subcat_id = request.form['subcategory']
        if request.form['name']:
            name = request.form['name']
        if request.form['description']:
            description = request.form['description']
        if request.form['price']:
            price = request.form['price']
        if request.files['file']:
            file = request.files['file']

        if file is None:
            # no picture provided
            if name and description and price:
                # all fields set: commit to database
                cat = session.query(Category).filter_by(id=cat_id).one()
                creator = getUserID(login_session['email'])
                Item1 = Item(user_id=creator.id, user=creator,
                             name=name, description=description,
                             price=price, cat_id=cat_id,
                             subcat_id=subcat_id, category=cat)
                session.add(Item1)
                session.commit()
                flash('A new item was created.')
                return redirect(url_for('showSubCategory',
                                        category_id=cat_id,
                                        subcategory_id=subcat_id))
            else:
                # form incomplete: form redrawn
                categories = session.query(Category).all()
                cat1 = session.query(Category).first()
                subcategories = session.query(
                    SubCategory).filter_by(cat_id=cat1.id)
                params = dict()
                params['categories'] = categories
                params['subcategories'] = subcategories
                user = getUserID(login_session['email'])
                params['user'] = user
                flash(
                    'Your form was incomplete. Please review the information')
                params['username'] = login_session['username']
                params['picture'] = login_session['picture']
                return render_template('newitem.html', **params)
        if file and allowed_file(file.filename):
            # file provided and in a valid format
            if name and description and price:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cat = session.query(Category).filter_by(id=cat_id).one()
                creator = getUserID(login_session['email'])
                Item1 = Item(
                    user_id=creator.id,
                    user=creator, name=name,
                    description=description,
                    img=filename,
                    price=price,
                    cat_id=cat_id,
                    subcat_id=subcat_id,
                    category=cat
                )
                flash(
                    'A new item was created.')
                session.add(Item1)
                session.commit()
                return redirect(url_for('showSubCategory',
                                        category_id=cat_id,
                                        subcategory_id=subcat_id))
            else:
                # file provided but not in one of the allowed formats
                categories = session.query(Category).all()
                cat1 = session.query(Category).first()
                subcategories = session.query(
                    SubCategory).filter_by(cat_id=cat1.id)
                params = dict()
                params['categories'] = categories
                params['subcategories'] = subcategories
                flash(
                    'Your form was incomplete. Please review the information')
                return render_template('newitem.html', **params)
        else:
            categories = session.query(Category).all()
            cat1 = session.query(Category).first()
            subcategories = session.query(
                SubCategory).filter_by(cat_id=cat1.id)
            params = dict()
            params['categories'] = categories
            params['subcategories'] = subcategories
            error_msg = 'Your picture was not valid. \
            Only png, jpg, jpeg, gif format allowed.'
            flash(error_msg)
            params['username'] = login_session['username']
            params['picture'] = login_session['picture']
            return render_template('newitem.html', **params)

    categories = session.query(Category).all()
    cat1 = session.query(Category).first()
    subcategories = session.query(SubCategory).filter_by(cat_id=cat1.id)
    params = dict()
    params['categories'] = categories
    params['subcategories'] = subcategories
    user = getUserID(login_session['email'])
    params['user'] = user
    params['picture'] = login_session['picture']
    return render_template('newitem.html', **params)


@app.route('/shop/<int:category_id>/new/', methods=['GET', 'POST'])
def newSubCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        file = None
        cat_id = None
        subcat_id = None
        name = None
        description = None

        if request.form['name']:
            name = request.form['name']
        if request.files['file']:
            file = request.files['file']

        if file is None:
            # form submitted without a picture: name is required
            if name:
                creator = getUserID(login_session['email'])
                SubCat1 = SubCategory(user_id=creator.id, user=creator,
                                      name=name,
                                      cat_id=category_id)
                session.add(SubCat1)
                session.commit()
                flash('A new subcategory was created.')
                return redirect(url_for('showCategories'))
            else:
                # no name provided: form must be resubmitted
                category = session.query(
                    Category).filter_by(id=category_id).one()
                params = dict()
                params['category'] = category
                flash(
                    'Your form was incomplete. Please review the information')
                user = getUserID(login_session['email'])
                params['user'] = user
                return render_template('newsubcategory.html', **params)
        if file and allowed_file(file.filename):
            # file provided and in the correct format
            if name:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['SUBCAT_FOLDER'], filename))
                creator = getUserID(login_session['email'])
                SubCat1 = SubCategory(user_id=creator.id,
                                      user=creator, name=name, image=filename,
                                      cat_id=category_id)
                session.add(SubCat1)
                session.commit()
                flash('A new subcategory was created.')
                return redirect(url_for('showCategories'))
            else:
                # no name for subcategory provided
                category = session.query(
                    Category).filter_by(id=category_id).one()
                params = dict()
                params['category'] = category
                flash(
                    'Your form was incomplete. Please review the information')
                params['username'] = login_session['username']
                params['picture'] = login_session['picture']
                return render_template('newsubcategory.html', **params)
        else:
            # image provided not in valid format
            category = session.query(Category).filter_by(id=category_id).one()
            params = dict()
            params['category'] = category
            error_msg = 'Your picture was not valid. \
            Only png, jpg, jpeg, gif format allowed.'
            flash(error_msg)
            params['username'] = login_session['username']
            params['picture'] = login_session['picture']
            return render_template('newsubcategory.html', **params)

    category = session.query(Category).filter_by(id=category_id).one()
    params = dict()
    params['category'] = category
    user = getUserID(login_session['email'])
    params['user'] = user
    params['picture'] = login_session['picture']
    return render_template('newsubcategory.html', **params)


@app.route('/')
@app.route('/shop/')
def showCategories():
    """ home page: show all categories """
    categories = session.query(Category).order_by(asc(Category.name))
    subcategories = session.query(SubCategory).order_by(asc(SubCategory.name))
    params = dict()
    params['categories'] = categories
    params['subcategories'] = subcategories
    if 'username' not in login_session:
        return render_template('publiccategories.html', **params)
    user = getUserID(login_session['email'])
    params['user'] = user
    params['picture'] = login_session['picture']
    return render_template('categories.html', **params)


@app.route('/shop/<int:category_id>/')
def showCategory(category_id):
    """ show all products in a category """
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(cat_id=category_id).all()
    subcategories = session.query(SubCategory).filter_by(cat_id=category_id)
    creator = getUserInfo(category.user_id)
    params = dict()
    params['items'] = items
    params['category'] = category
    params['creator'] = creator
    params['subcategories'] = subcategories
    if 'username' not in login_session:
        return render_template('publiccategory.html', **params)
    user = getUserID(login_session['email'])
    params['user'] = user
    params['login_session'] = login_session
    params['picture'] = login_session['picture']
    return render_template('category.html', **params)


@app.route('/shop/<int:category_id>/<int:subcategory_id>/')
def showSubCategory(category_id, subcategory_id):
    """ show all products in a subcategory """
    items = session.query(Item).filter_by(subcat_id=subcategory_id).all()
    subcategory = session.query(SubCategory).filter_by(id=subcategory_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(category.user_id)
    params = dict()
    params['items'] = items
    params['category'] = category
    params['creator'] = creator
    params['subcategory'] = subcategory
    if 'username' not in login_session:
        return render_template('publicsubcategory.html', **params)
    user = getUserID(login_session['email'])
    params['user'] = user
    params['username'] = login_session['username']
    params['picture'] = login_session['picture']
    return render_template('subcategory.html', **params)


@app.route('/shop/<int:category_id>/<int:subcategory_id>/<int:product_id>')
def showItem(category_id, subcategory_id, product_id):
    """ show a single product """
    item = session.query(Item).filter_by(id=product_id).one()
    subcategory = session.query(SubCategory).filter_by(id=subcategory_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(item.user_id)
    params = dict()
    params['item'] = item
    params['category'] = category
    params['creator'] = creator
    params['subcategory'] = subcategory
    if 'username' not in login_session:
        return render_template('publicsingle.html', **params)
    else:
        user = getUserID(login_session['email'])
        params['user'] = user
        params['username'] = login_session['username']
        params['picture'] = login_session['picture']
        if creator.email == login_session['email']:
            return render_template('single.html', **params)
        else:
            return render_template('publicsingle.html', **params)


@app.route('/shop/<int:category_id>/<int:subcategory_id>/ \
    <int:product_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, subcategory_id, product_id):
    editedItem = session.query(Item).filter_by(id=product_id).one()
    categories = session.query(Category).all()
    subcategories = session.query(SubCategory).filter_by(cat_id=category_id)
    if 'username' not in login_session:
        return redirect('/login')
    params = dict()
    params['username'] = login_session['username']
    params['user_id'] = login_session['user_id']
    params['picture'] = login_session['picture']
    editor = getUserID(login_session['email'])
    if editor.id == editedItem.user_id:
        if request.method == 'POST':
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['price']:
                editedItem.price = request.form['price']
            if request.form['category']:
                editedItem.cat_id = request.form['category']
            if request.form['subcategory']:
                editedItem.subcat_id = request.form['subcategory']
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
            params['product_id'] = editedItem.id
            params['category'] = editedItem.cat_id
            params['subcat_id'] = editedItem.subcat_id
            return redirect(url_for('showItem',
                                    category_id=editedItem.cat_id,
                                    subcategory_id=editedItem.subcat_id,
                                    product_id=editedItem.id))
        else:
            return render_template('edititem.html',
                                   item=editedItem,
                                   categories=categories,
                                   subcategories=subcategories)
    else:
        return "you are not allowed to edit this item"


@app.route('/shop/<int:category_id>/<int:subcategory_id>/edit',
           methods=['GET', 'POST'])
def editSubCategory(category_id, subcategory_id):
    subcategory = session.query(SubCategory).filter_by(id=subcategory_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    params = dict()
    params['username'] = login_session['username']
    user = getUserID(login_session['email'])
    params['user'] = user
    params['picture'] = login_session['picture']
    if user.id == subcategory.user_id:
        if request.method == 'POST':
            subcategory.name = request.form['name']
            session.add(subcategory)
            session.commit()
            flash('successfully edited subcategory')
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            params['subcategory'] = subcategory
            params['category_id'] = category_id
            params['subcategory_id'] = subcategory_id
            return render_template('editsubcategory.html', **params)
    else:
        return "you are not allowed to edit this subcategory"


@app.route('/changepic/<int:product_id>/', methods=['GET', 'POST'])
def changePic(product_id):
    """ change image for a product/ad """
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(id=product_id).one()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if item.img:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.img))
            item.img = filename
            session.add(item)
            session.commit()
            return redirect(url_for('showItem',
                                    category_id=item.cat_id,
                                    subcategory_id=item.subcat_id,
                                    product_id=item.id))
    return render_template('changepic.html', item=item)


@app.route('/changesubcatpic/<int:subcategory_id>/', methods=['GET', 'POST'])
def changesubcatpic(subcategory_id):
    """ change image for a subcategory """
    if 'username' not in login_session:
        return redirect('/login')
    subcat = session.query(SubCategory).filter_by(id=subcategory_id).one()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['SUBCAT_FOLDER'], filename))
            if subcat.image:
                os.remove(
                    os.path.join(app.config['SUBCAT_FOLDER'], subcat.image))
            subcat.image = filename
            session.add(subcat)
            session.commit()
            flash("Picture changed")
            subcat = session.query(SubCategory).filter_by(
                id=subcategory_id).one()
            return redirect(url_for('showCategory',
                                    category_id=subcat.cat_id))
    params = dict()
    params['subcat'] = subcat
    user = getUserID(login_session['email'])
    params['user'] = user
    return render_template('changesubcatpic.html', **params)


@app.route('/shop/<int:category_id>/<int:subcategory_id>/delete',
           methods=['GET', 'POST'])
def deleteSubCategory(category_id, subcategory_id):
    """ delete a subcategory """
    subcatToDelete = session.query(
        SubCategory).filter_by(id=subcategory_id).one()
    cat_id = subcatToDelete.cat_id
    if 'username' not in login_session:
        return redirect('/login')
    user = getUserID(login_session['email'])
    if subcatToDelete.user_id == user.id:
        if request.method == 'POST':
            session.delete(subcatToDelete)
            session.commit()
            flash('Subcategory Successfully Deleted')
            print 'item successfully deleted'
            return redirect(url_for('showCategory', category_id=cat_id))
        else:
            return render_template('deleteMenuItem.html', item=itemToDelete)
    else:
        return "you are not allowed to delete this subcategory"


# Delete an item
@app.route('/shop/<int:category_id>/<int:subcategory_id>/ \
        <int:product_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, subcategory_id, product_id):
    """ delete an item """
    itemToDelete = session.query(Item).filter_by(id=product_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        user = getUserID(login_session['email'])
        if user.id == itemToDelete.user_id:
            session.delete(itemToDelete)
            session.commit()
            flash('Post Successfully Deleted')
            print 'item successfully deleted'
            return redirect(url_for('showCategories'))
        else:
            return "you are not allowed to delete this item"


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
