from resin import Resin
from resin import exceptions as resin_exceptions
from resin import Token


class TestHelper(object):

    credential = {
        'email': 'pythonsdktest@gmail.com',
        'password': 'resintest',
        'user_id': 'g_account_test'
    }

    resin = Resin()

    def __init__(self):
        self.resin_exceptions = resin_exceptions
        if not self.resin.auth.is_logged_in():
            self.resin.auth.login(
                **{
                    'username': self.credential['user_id'],
                    'password': self.credential['password']
                }
            )

        # Stop the test if it's run by an admin user account.
        token = Token()
        if any('admin' in s for s in token.get_data()['permissions']):
            raise Exception('The test is run with an admin user account. Cancelled, please try again with a normal account!')

    def wipe_application(self):
        """
        Wipe all user's apps
        """

        self.resin.models.application.base_request.request(
            'application', 'DELETE',
            endpoint=self.resin.settings.get('pine_endpoint'), login=True
        )

    def reset_user(self):
        """
        Wipe all user's apps and ssh keys added.
        """

        print(self.resin.auth.who_am_i())
        if self.resin.auth.is_logged_in():
            self.wipe_application()
            self.resin.models.key.base_request.request(
                'user__has__public_key', 'DELETE',
                endpoint=self.resin.settings.get('pine_endpoint'), login=True
            )
