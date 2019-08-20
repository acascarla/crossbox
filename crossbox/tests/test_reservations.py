import datetime
from freezegun import freeze_time
from http import HTTPStatus
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User

from .constants import EXPECTED_RESERVATION_DAYS
from crossbox.models import Session, Reservation
from crossbox.constants import MAX_RESERVATION_PLACES


class ReservationsCase(TestCase):

    fixtures = ['tests_auth', 'tests_base']

    def setUp(self):
        self.client = Client()
        self.client.login(username='admin', password='admin')
        self.user_id = next(iter(self.client.session.items()))[1]
        self.user = User.objects.get(id=self.user_id)

    def test_login(self):
        self.assertIn('_auth_user_id', self.client.session)

    @freeze_time('2019-05-14')
    def test_reservation_view(self):
        response = self.client.get(reverse('reservation'))
        context = response.context
        expected_hours = [
            {'id': 3, 'hour': datetime.time(10, 0)},
            {'id': 4, 'hour': datetime.time(11, 0)},
            {'id': 5, 'hour': datetime.time(12, 0)},
            {'id': 6, 'hour': datetime.time(13, 0)},
            {'id': 10, 'hour': datetime.time(17, 0)},
            {'id': 11, 'hour': datetime.time(18, 0)},
            {'id': 12, 'hour': datetime.time(19, 0)},
            {'id': 13, 'hour': datetime.time(20, 0)}
        ]
        context_hours = [dict(h) for h in context['hours'].values()]
        self.assertEquals(context_hours, expected_hours)
        self.assertEquals(context['days'], EXPECTED_RESERVATION_DAYS)
        self.assertEquals(context['wods'], 1)
        self.assertEquals(context['page'], 0)

    def test_reservation_create_no_wods(self):
        # New users have always 1 initial free wod, let's spend it
        self.reservation_view_test(
            mode='create',
            session_id=2,
            status_code_expected=HTTPStatus.OK,
            result_expected='created',
        )
        # Now test no_wod functionality
        self.reservation_view_test(
            mode='create',
            session_id=3,
            status_code_expected=HTTPStatus.FORBIDDEN,
            result_expected='no_wods',
        )

    def test_reservation_create_already_reserved(self):
        # Reservate first time
        self.reservation_view_test(
            mode='create',
            session_id=2,
            status_code_expected=HTTPStatus.OK,
            result_expected='created',
        )
        # Now test reservate second time on same session
        self.user.subscriber.wods += 1
        self.user.subscriber.save()
        self.reservation_view_test(
            mode='create',
            session_id=2,
            status_code_expected=HTTPStatus.FORBIDDEN,
            result_expected='already_reserved',
        )

    def test_reservation_create_max_reservations(self):
        session = Session.objects.get(pk=2)
        users = User.objects.bulk_create([
            User(username=f'user_{i}')
            for i in range(MAX_RESERVATION_PLACES)
        ])
        for i in range(MAX_RESERVATION_PLACES):
            Reservation.objects.create(session=session, user=users[i])
        self.reservation_view_test(
            mode='create',
            session_id=2,
            status_code_expected=HTTPStatus.FORBIDDEN,
            result_expected='max_reservations',
        )

    def test_reservation_create_closed_session(self):
        """
        when:
        - now is after the begining of the session
        then:
        - returns a FORBIDDEN response with 'closed_session' result
        """
        pass  # TODO

    def test_reservation_create_ok(self):
        self.assertEquals(self.user.subscriber.wods, 1)
        self.reservation_view_test(
            mode='create',
            session_id=2,
            status_code_expected=HTTPStatus.OK,
            result_expected='created',
        )
        self.user.subscriber.refresh_from_db()
        self.assertEquals(self.user.subscriber.wods, 0)

    def reservation_view_test(
            self, mode, session_id, status_code_expected, result_expected):
        response = self.client.post(
            path=reverse(f'reservation-{mode}'),
            data={'session': session_id},
            content_type='application/json',
        )
        self.assertEquals(response.status_code, status_code_expected)
        self.assertEquals(response.json()['result'], result_expected)

    def test_reservation_delete_session_not_found(self):
        self.reservation_view_test(
            mode='delete',
            session_id=12345,
            status_code_expected=HTTPStatus.NOT_FOUND,
            result_expected='session_not_found',
        )

    @freeze_time('2018-12-31 8:00:00')
    def test_reservation_delete_no_subscriber(self):
        """
        given:
        - a request to delete a reservation arrives
        when:
        - user has no subscriber, so can't refund the wod
        then:
        - returns a FORBIDDEN response with 'no_subscriber' result
        """
        pass  # TODO

    @freeze_time('2018-12-30 10:00:00')
    def test_reservation_delete_reservation_not_found(self):
        self.reservation_view_test(
            mode='delete',
            session_id=2,
            status_code_expected=HTTPStatus.NOT_FOUND,
            result_expected='no_reservation',
        )

    def test_reservation_delete_unhandled_error(self):
        """
        given:
        - a request to delete a reservation arrives
        when:
        - any other kind of error happened
        then:
        - returns a FORBIDDEN response with 'unhandled' result
        """
        pass  # TODO

    @freeze_time('2019-01-01 17:01:00')
    @patch('django.db.models.QuerySet.count')
    def test_reservation_delete_is_too_late(self, QuerySetCountMock):
        # session 21 -> day: 2019-01-02, hour: 17:00:00
        QuerySetCountMock.return_value = 5
        self.reservation_view_test(
            mode='delete',
            session_id=21,
            status_code_expected=HTTPStatus.FORBIDDEN,
            result_expected='is_too_late',
        )

    @freeze_time('2019-01-01 17:01:00')
    @patch('django.db.models.QuerySet.count')
    def test_reservation_delete_ok_is_too_late_but_few_people(
            self, QuerySetCountMock):
        # session 21 -> day: 2019-01-02, hour: 17:00:00
        QuerySetCountMock.return_value = 4
        self.reservation_view_test(
            mode='delete',
            session_id=21,
            status_code_expected=HTTPStatus.OK,
            result_expected='deleted',
        )
        self.user.subscriber.refresh_from_db()
        self.assertEquals(self.user.subscriber.wods, 2)

    @freeze_time('2019-01-01 17:00:00')
    @patch('django.db.models.QuerySet.count')
    def test_reservation_delete_ok(
            self, QuerySetCountMock):
        # session 21 -> day: 2019-01-02, hour: 17:00:00
        QuerySetCountMock.return_value = 10
        self.reservation_view_test(
            mode='delete',
            session_id=21,
            status_code_expected=HTTPStatus.OK,
            result_expected='deleted',
        )
        self.user.subscriber.refresh_from_db()
        self.assertEquals(self.user.subscriber.wods, 2)
