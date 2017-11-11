from resin import Resin
from resin import exceptions as resin_exceptions


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
