import unittest
from application import app, db
from application.models import User

class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        user = User(username='jake')
        user.set_password('test_password')
        self.assertFalse(user.check_password('wrong_password'))
        self.assertTrue(user.check_password('test_password'))

    def test_avatar(self):
        user = User(username='john', email='john@example.com')
        self.assertEqual(user.avatar(128), ('https://www.gravatar.com/avatar/'
                                            'd4c74594d841139328695756648b6bd6'
                                            '?d=identicon&s=128'))

    def test_change_username(self):
        user = User(username='jake', email='jake@example.com')

    def test_follow(self):
        user1 = User(username='jake', email='jake@example.com')
        user2 = User(username='lissy', email='lissy@example.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        self.assertEqual(user1.followed_by.all(), [])
        self.assertEqual(user2.followed_by.all(), [])

        user1.follow(user2)     # jake follows lissy
        db.session.commit()

        self.assertTrue(user1.is_following(user2))
        self.assertEqual(user1.followed_users.count(), 1)
        self.assertEqual(user1.followed_users.first().username, 'lissy')

        self.assertEqual(user2.followed_by.count(), 1)
        self.assertEqual(user2.followed_by.first().username, 'jake')

        user1.unfollow(user2)
        db.session.commit()
        self.assertFalse(user1.is_following(user2))
        self.assertEqual(user1.followed_users.count(), 0)
        self.assertEqual(user2.followed_by.count(), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)