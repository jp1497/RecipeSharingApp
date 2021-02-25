from application import login, db, app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import jwt

followers = db.Table('followers',
                     db.Column('user_following_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('user_being_followed_by_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    # Setup the data points for the user model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(128))

    # creates followed / following relationship between Users
    followed_users = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.user_following_id == id),
        secondaryjoin=(followers.c.user_being_followed_by_id == id),
        back_populates='followed_by',
        lazy='dynamic'
    )

    followed_by = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.user_being_followed_by_id == id),
        secondaryjoin=(followers.c.user_following_id == id),
        back_populates='followed_users',
        lazy='dynamic'
    )

    # setup relationship to recipes:
    uploaded_recipes = db.relationship('Recipe', back_populates='author')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        # returns an encoded jwt token
        return jwt.encode(
            {'reset_password': self.id, 'exp': time()+expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        # takes a token and attempts to decode it.
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            # if token is invalid or expired, catch error and return None
            return
        return User.query.get(id)

    def avatar(self, size):
        # convert email to lowercase then convert to bytes and encode as utf-8
        # generate an md5 hash (only works on bytes, not strings)
        md5hash = md5(self.email.lower().encode('utf-8')).hexdigest()
        # return gravatar profile image for the user's email address
        # d = default gravatar image for users without a profile, s = size of image
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            md5hash, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed_users.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed_users.remove(user)

    # looks in follower association table for entries which link the current user with the
    # user passed in as a parameter
    def is_following(self, user):
        return self.followed_users.filter(followers.c.user_being_followed_by_id == user.id).count() > 0

    def get_recipes(self):
        return self.uploaded_recipes


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(16))
    description = db.Column(db.String(64))
    cooking_time = db.Column(db.Integer)
    rating = db.Column(db.Integer)
    img_path = db.Column(db.String(64))
    category = db.Column(db.String(64)) # update to db object later

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    author = db.relationship('User', back_populates='uploaded_recipes')

    ingredients_used = db.relationship('RecipeIngredient', back_populates='recipe', lazy='dynamic')


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(32))
    img_path = db.Column(db.String(64))
    used_in_recipes = db.relationship('RecipeIngredient', back_populates='ingredient', lazy='dynamic')


class RecipeIngredient(db.Model):
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)

    quantity = db.Column(db.Integer)
    unit = db.Column(db.String(16))

    recipe = db.relationship('Recipe', back_populates='ingredients_used')
    ingredient = db.relationship('Ingredient', back_populates='used_in_recipes')


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
