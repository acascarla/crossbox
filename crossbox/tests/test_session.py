import datetime
from http import HTTPStatus
from freezegun import freeze_time

from django.test import TestCase
from django.urls import reverse

from crossbox.tests.tools import with_login, create_session
from crossbox.models.hour import Hour
from crossbox.models.track import Track
from crossbox.models.session import Session
from crossbox.models.session_type import SessionType
from crossbox.models.capacity_limit import CapacityLimit
from crossbox.admin.session import SessionAdmin, SessionAdminFilter


class SessionsCase(TestCase):

    fixtures = [
        'users', 'capacity_limits', 'session_types', 'tracks', 'subscribers',
        'week_templates', 'hours'
    ]

    @with_login()
    def test_change_session_type(self):
        hour = Hour(hour=datetime.time(0, 0))
        hour.save()
        day = datetime.date(year=2019, month=1, day=1)
        session = Session(
            date=day,
            hour=hour,
            session_type=SessionType.objects.get(pk=1),
            capacity_limit=CapacityLimit.objects.get(pk=1),
            track=Track.objects.get(pk=1),
        )
        session.save()
        self._session_view_test(
            session_id=session.id,
            status_code_expected=HTTPStatus.OK,
            result_expected={'pk': 2, 'name': 'OPEN'},
        )
        self._session_view_test(
            session_id=session.id,
            status_code_expected=HTTPStatus.OK,
            result_expected={'pk': 3, 'name': 'ESTIRAMIENTOS'},
        )
        self._session_view_test(
            session_id=session.id,
            status_code_expected=HTTPStatus.OK,
            result_expected={'pk': 1, 'name': 'WOD'},
        )
        self._session_view_test(
            session_id=session.id,
            status_code_expected=HTTPStatus.OK,
            result_expected={'pk': 2, 'name': 'OPEN'},
        )

    @with_login()
    @freeze_time('2020-01-1')
    def test_session_template_context_data_weeks(self):
        response = self.client.get(path=reverse('session-template'))
        weeks = response.context_data['weeks']
        self.assertEqual(len(weeks), 52)
        self.assertEqual(weeks[0], 'Lunes 30/12/2019 - Semana 1 (actual)')
        self.assertEqual(weeks[51], 'Lunes 21/12/2020 - Semana 52')

    @with_login()
    def test_change_session_type_no_session(self):
        response = self.client.put(
            path=reverse('change_session_type', args=[13371337]))
        self.assertEquals(response.status_code, HTTPStatus.NOT_FOUND)

    @with_login()
    @freeze_time('2020-01-01')
    def test_change_session_type_db_types(self):
        """Check types are taken from database"""
        SessionType.objects.create(name='new_type')
        session = create_session()  # session_type WOD
        path = reverse('change_session_type', args=[session.pk])
        _ = self.client.put(path=path)  # session_type OPEN
        _ = self.client.put(path=path)  # session_type ESTIRAMIENTOS
        response = self.client.put(path=path)
        self.assertEquals(
            response.json()['session_type'], {'pk': 4, 'name': 'new_type'}
        )

    @with_login()
    def test_gen_sessions_invalid_post_params(self):
        path = reverse('generate-sessions')
        kwargs = {
            'page': None,
            'week_template': 1,
            'track': 1,
            'capacity_limit': 1,
        }
        with self.assertRaises(Exception):
            self.client.post(path=path, data=kwargs)
        kwargs['page'] = 1
        kwargs['week_template'] = None
        with self.assertRaises(Exception):
            self.client.post(path=path, data=kwargs)
        kwargs['week_template'] = 1
        kwargs['track'] = None
        with self.assertRaises(Exception):
            self.client.post(path=path, data=kwargs)
        kwargs['track'] = 1
        kwargs['capacity_limit'] = None
        with self.assertRaises(Exception):
            self.client.post(path=path, data=kwargs)
        kwargs['capacity_limit'] = 1
        self.client.post(path=path, data=kwargs)  # no raise

    @with_login()
    def test_gen_sessions_delete_same_track_sessions(self):
        pass

    @with_login()
    def test_gen_sessions_new_sessions_for_that_week(self):
        pass

    @with_login()
    def test_gen_sessions_redirect_created_week_page(self):
        pass

    def _session_view_test(
        self, session_id, status_code_expected, result_expected
    ):
        response = self.client.put(
            path=reverse('change_session_type', args=[session_id]))
        self.assertEquals(response.status_code, status_code_expected)
        self.assertEquals(response.json()['session_type'], result_expected)


class SessionAdminFilterCase(TestCase):

    fixtures = ['capacity_limits', 'session_types', 'tracks']

    @freeze_time('2020-02-1')
    def test_queryset_depending_on_filter_selected(self):
        hour = Hour(hour=datetime.time(0, 0))
        hour.save()
        kwargs = {
            'hour': hour,
            'session_type': SessionType.objects.get(pk=1),
            'capacity_limit': CapacityLimit.objects.get(pk=1),
            'track': Track.objects.get(pk=1),
        }
        day_jan = datetime.date(year=2020, month=1, day=1)
        day_feb = datetime.date(year=2020, month=2, day=1)
        day_mar = datetime.date(year=2020, month=3, day=1)
        Session.objects.bulk_create([
            Session(date=day_jan, **kwargs),
            Session(date=day_feb, **kwargs),
            Session(date=day_mar, **kwargs),
        ])
        session_filter = SessionAdminFilter(None, {}, Session, SessionAdmin)
        session_filter.used_parameters['filter'] = None
        from_this_week_sessions = session_filter.queryset(
            None, Session.objects.all())
        self.assertEquals(from_this_week_sessions[0].date, day_feb)
        self.assertEquals(from_this_week_sessions[1].date, day_mar)
        self.assertEquals(from_this_week_sessions.count(), 2)

        session_filter.used_parameters['filter'] = 'past'
        past_sessions = session_filter.queryset(None, Session.objects.all())
        self.assertEquals(past_sessions[0].date, day_jan)
        self.assertEquals(past_sessions.count(), 1)

        session_filter.used_parameters['filter'] = 'all_desc'
        all_desc_sessions = session_filter.queryset(
            None, Session.objects.all())
        self.assertEquals(all_desc_sessions[0].date, day_mar)
        self.assertEquals(all_desc_sessions[1].date, day_feb)
        self.assertEquals(all_desc_sessions[2].date, day_jan)

        session_filter.used_parameters['filter'] = 'all_asc'
        all_asc_sessions = session_filter.queryset(None, Session.objects.all())
        self.assertEquals(all_asc_sessions[0].date, day_jan)
        self.assertEquals(all_asc_sessions[1].date, day_feb)
        self.assertEquals(all_asc_sessions[2].date, day_mar)
