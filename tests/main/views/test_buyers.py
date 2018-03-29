# coding: utf-8
from __future__ import unicode_literals

from ...helpers import BaseApplicationTest
from dmapiclient import api_stubs, HTTPError
from dmcontent.content_loader import ContentLoader
import mock
from lxml import html
import pytest

from app.main.views import buyers
from freezegun import freeze_time
import functools


po = functools.partial(mock.patch.object, autospec=True)


def find_briefs_mock():
    base_brief_values = {
        "createdAt": "2016-02-01T00:00:00.000000Z",
        "frameworkSlug": "digital-outcomes-and-specialists-2",
        "frameworkFramework": "digital-outcomes-and-specialists",
        "lot": "digital-specialists"
    }

    find_briefs_response = {
        "briefs": [
            {
                "id": 20,
                "status": "draft",
                "title": "A draft brief"
            }, {
                "id": 21,
                "status": "live",
                "title": "A live brief",
                "publishedAt": "2016-02-04T12:00:00.000000Z"
            }, {
                "id": 22,
                "status": "closed",
                "title": "A closed brief with brief responses",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-21T12:01:00.000000Z"
            }, {
                "id": 23,
                "status": "withdrawn",
                "title": "A withdrawn brief",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "withdrawnAt": "2016-02-05T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-20T12:00:00.000000Z"
            }, {
                "id": 24,
                "status": "awarded",
                "title": "An awarded brief",
                "publishedAt": "2016-02-03T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-19T12:00:00.000000Z"
            }, {
                "id": 25,
                "status": "closed",
                "title": "A closed brief with no brief responses",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-18T12:00:00.000000Z"
            },
            {
                "id": 26,
                "status": "cancelled",
                "title": "A cancelled brief",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-17T12:00:00.000000Z"
            },
            {
                "id": 27,
                "status": "unsuccessful",
                "title": "An unsuccessful brief where no suitable suppliers applied",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-16T12:00:00.000000Z"
            },
        ]
    }

    for brief in find_briefs_response['briefs']:
        brief.update(base_brief_values)

    return find_briefs_response


class TestBuyerDashboard(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()
        self.data_api_client.find_briefs.return_value = find_briefs_mock()
        self.login_as_buyer()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_draft_briefs_section(self):
        res = self.client.get(self.briefs_dashboard_url)
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')

        assert res.status_code == 200

        draft_row = [cell.text_content().strip() for cell in tables[0].xpath('.//tbody/tr/td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/20'

        assert draft_row[0] == "A draft brief"
        assert tables[0].xpath('.//tbody/tr')[0].xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert draft_row[1] == "Monday 1 February 2016"

    def test_live_briefs_section(self):
        res = self.client.get(self.briefs_dashboard_url)
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')

        assert res.status_code == 200

        live_row = [cell.text_content().strip() for cell in tables[1].xpath('.//tbody/tr/td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/21'

        assert live_row[0] == "A live brief"
        assert tables[1].xpath('.//tbody/tr')[0].xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert live_row[1] == "Thursday 4 February 2016"

    def test_closed_briefs_section_with_closed_brief(self):
        res = self.client.get(self.briefs_dashboard_url)

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        closed_row_cells = tables[2].xpath('.//tbody/tr')[0].xpath('.//td')

        assert closed_row_cells[0].xpath('.//a')[0].text_content() == "A closed brief with brief responses"
        assert closed_row_cells[0].xpath('.//a/@href')[0] == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/22'

        assert tables[2].xpath('.//tbody/tr/td')[1].text_content().strip() == "Sunday 21 February 2016"

        assert closed_row_cells[2].xpath('.//a')[0].text_content() == "View responses"
        assert closed_row_cells[2].xpath('.//a/@href')[0] == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/22/responses'

        assert closed_row_cells[2].xpath('.//a')[1].text_content() == "Let suppliers know the outcome"
        assert closed_row_cells[2].xpath('.//a/@href')[1] == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/22/award'

    def test_closed_briefs_section_with_withdrawn_brief(self):
        res = self.client.get(self.briefs_dashboard_url)

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        withdrawn_row = tables[2].xpath('.//tbody/tr')[1]
        withdrawn_row_cells = [cell.text_content().strip() for cell in withdrawn_row.xpath('.//td')]
        expected_link = '/digital-outcomes-and-specialists/opportunities/23'

        assert withdrawn_row_cells[0] == "A withdrawn brief"
        assert withdrawn_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert withdrawn_row_cells[1] == "Withdrawn"
        assert "View responses" not in withdrawn_row_cells[2]
        assert "Let suppliers know the outcome" not in withdrawn_row_cells[2]

    def test_closed_briefs_section_with_awarded_brief(self):
        res = self.client.get(self.briefs_dashboard_url)

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        awarded_row = tables[2].xpath('.//tbody/tr')[2]
        awarded_row_cells = [cell.text_content().strip() for cell in awarded_row.xpath('.//td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/24'

        assert awarded_row_cells[0] == "An awarded brief"
        assert awarded_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert awarded_row_cells[1] == "Friday 19 February 2016"
        assert "View responses" not in awarded_row_cells[2]
        assert "Let suppliers know the outcome" not in awarded_row_cells[2]

    def test_closed_briefs_section_with_cancelled_brief(self):
        res = self.client.get(self.briefs_dashboard_url)

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        cancelled_row = tables[2].xpath('.//tbody/tr')[4]
        cancelled_row_cells = [cell.text_content().strip() for cell in cancelled_row.xpath('.//td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/26'

        assert cancelled_row_cells[0] == "A cancelled brief"
        assert cancelled_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert cancelled_row_cells[1] == "Wednesday 17 February 2016"
        assert "View responses" not in cancelled_row_cells[2]
        assert "Let suppliers know the outcome" not in cancelled_row_cells[2]

    def test_closed_briefs_section_with_unsuccessful_brief(self):
        res = self.client.get(self.briefs_dashboard_url)

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        unsuccessful_row = tables[2].xpath('.//tbody/tr')[5]
        unsuccessful_row_cells = [cell.text_content().strip() for cell in unsuccessful_row.xpath('.//td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/27'

        assert unsuccessful_row_cells[0] == "An unsuccessful brief where no suitable suppliers applied"
        assert unsuccessful_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert unsuccessful_row_cells[1] == "Tuesday 16 February 2016"
        assert "View responses" not in unsuccessful_row_cells[2]
        assert "Let suppliers know the outcome" not in unsuccessful_row_cells[2]


class TestBuyerRoleRequired(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_login_required_for_buyer_pages(self):
        res = self.client.get(self.briefs_dashboard_url)
        assert res.status_code == 302
        assert res.location == 'http://localhost/user/login?next={}'.format(
            self.briefs_dashboard_url.replace('/', '%2F')
        )

    def test_supplier_cannot_access_buyer_pages(self):
        self.login_as_supplier()
        res = self.client.get(self.briefs_dashboard_url)
        assert res.status_code == 302
        assert res.location == 'http://localhost/user/login?next={}'.format(
            self.briefs_dashboard_url.replace('/', '%2F')
        )
        self.assert_flashes('You must log in with a buyer account to see this page.', expected_category='error')

    def test_buyer_pages_ok_if_logged_in_as_buyer(self):
        self.login_as_buyer()
        res = self.client.get(self.briefs_dashboard_url)
        page_text = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements' in page_text


class TestStartNewBrief(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.login_as_buyer()
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_show_start_brief_page(self):
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

        assert res.status_code == 200

    def test_404_if_lot_does_not_allow_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

        assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

            assert res.status_code == 404

    def test_404_if_lot_does_not_exist(self):
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses/create")

        assert res.status_code == 404


class TestCreateNewBrief(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()
        self.login_as_buyer()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_create_new_digital_specialists_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": "Title"
            })

        assert res.status_code == 302
        self.data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )

    def test_create_new_digital_outcomes_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/create",
            data={
                "title": "Title"
            })

        assert res.status_code == 302
        self.data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-outcomes',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )

    def test_404_if_lot_does_not_allow_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "specialistRole": "agileCoach"
            })

        assert res.status_code == 404
        assert not self.data_api_client.create_brief.called

    def test_404_if_framework_status_is_not_live(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "specialistRole": "agileCoach"
            })

        assert res.status_code == 404
        assert not self.data_api_client.create_brief.called

    def test_404_if_lot_does_not_exist(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses/create",
            data={
                "specialistRole": "agileCoach"
            })

        assert res.status_code == 404
        assert not self.data_api_client.create_brief.called

    def test_400_if_form_error(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        self.data_api_client.create_brief.side_effect = HTTPError(
            mock.Mock(status_code=400),
            {"title": "answer_required"})

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": "Title"
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        anchor = document.cssselect('div.validation-masthead a[href="#title"]')

        assert len(anchor) == 1
        assert "Title" in anchor[0].text_content().strip()
        self.data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )


class TestCopyBrief(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.login_as_buyer()
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.brief = api_stubs.brief(
            framework_slug="digital-outcomes-and-specialists-2",
            framework_name="Digital Outcomes and Specialists 2"
        )
        self.data_api_client.get_brief.return_value = self.brief

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_get_not_allowed(self):
        res = self.client.get(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        assert res.status_code == 404

    def test_copy_brief_and_redirect_to_copied_brief_edit_title_page(self):
        new_brief = self.brief.copy()
        new_brief["briefs"]["id"] = 1235
        self.data_api_client.copy_brief.return_value = new_brief

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        self.data_api_client.copy_brief.assert_called_once_with('1234', 'buyer@email.com')

        assert res.location == (
            "http://localhost/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/"
            "1235/edit/title/title"
        )

    def test_copy_brief_for_expired_framework_redirects_to_edit_page_for_new_framework(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief()  # dos1 brief

        new_brief = self.brief.copy()  # dos2 brief
        new_brief["briefs"]["id"] = 1235
        self.data_api_client.copy_brief.return_value = new_brief

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/copy'
        )

        assert res.location == (
            "http://localhost/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/"
            "1235/edit/title/title"
        )

    @mock.patch("app.main.views.buyers.is_brief_correct", autospec=True)
    def test_404_if_brief_is_not_correct(self, is_brief_correct):
        is_brief_correct.return_value = False

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        assert res.status_code == 404
        is_brief_correct.assert_called_once_with(
            self.brief["briefs"],
            "digital-outcomes-and-specialists-2",
            "digital-specialists",
            123,
            allow_withdrawn=True
        )

    def test_can_copy_withdrawn_brief(self):
        # Make our original brief withdrawn
        withdrawn_brief = self.brief.copy()
        withdrawn_brief["briefs"].update({'status': 'withdrawn'})
        self.data_api_client.get_brief.return_value = withdrawn_brief

        # Set copied brief return
        new_brief = self.brief.copy()  # dos2 brief
        new_brief["briefs"]["id"] = 1235
        self.data_api_client.copy_brief.return_value = new_brief

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        # Assert redirect and copy_brief call
        assert res.status_code == 302
        self.data_api_client.copy_brief.assert_called_once_with('1234', 'buyer@email.com')


class TestEditBriefSubmission(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_brief.return_value = api_stubs.brief()
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        self.login_as_buyer()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def _test_breadcrumbs_on_question_page(self, response, has_summary_page=False, section_name=None):
        extra_breadcrumbs = [
            ('I need a thing to do a thing',
             '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234')
        ]
        if has_summary_page and section_name:
            extra_breadcrumbs.append((
                section_name,
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/{}'.format(
                    section_name.lower().replace(' ', '-')
                )
            ))

        self.assert_breadcrumbs(response, extra_breadcrumbs)

    def test_edit_brief_submission(self):
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Organisation the work is for"

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_return_link_to_section_summary_if_section_has_description(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-4/optional2")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Optional 2"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to section 4"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=True, section_name='Section 4')

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_return_link_to_section_summary_if_other_questions(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-1/required1")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Required 1"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to section 1"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=True, section_name='Section 1')

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_return_link_to_brief_overview_if_single_question(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-2/required2")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Required 2"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to overview"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=False)

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_multiquestion(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/section-5/required3")  # noqa

        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Required 3"
        assert document.xpath(
            '//*[@id="required3_1"]//span[contains(@class, "question-heading")]'
        )[0].text_content().strip() == "Required 3_1"
        assert document.xpath(
            '//*[@id="required3_2"]//span[contains(@class, "question-heading")]'
        )[0].text_content().strip() == "Required 3_2"

    def test_404_if_brief_does_not_belong_to_user(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_lot_does_not_allow_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_lot_does_not_exist(self):
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_post_brief_has_wrong_lot(self):
        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses"
            "/1234/edit/description-of-work/organisation",
            data={"organisation": True}
        )

        assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
                "/1234/edit/description-of-work/organisation")

            assert res.status_code == 404

    def test_404_if_brief_has_published_status(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(status='published')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_section_does_not_exist(self):
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/not-a-real-section")

        assert res.status_code == 404

    def test_404_if_question_does_not_exist(self):
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/not-a-real-question")

        assert res.status_code == 404


class TestUpdateBriefSubmission(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_brief.return_value = api_stubs.brief()
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        self.login_as_buyer()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_update_brief_submission(self):
        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 302
        self.data_api_client.update_brief.assert_called_with(
            '1234',
            {"organisation": "GDS"},
            page_questions=['organisation'],
            updated_by='buyer@email.com'
        )

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_post_update_if_multiple_questions_redirects_to_section_summary(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-1/required1",
            data={
                "required1": True
            })

        assert res.status_code == 302
        self.data_api_client.update_brief.assert_called_with(
            '1234',
            {"required1": True},
            page_questions=['required1'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1'
        ) is True

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_post_update_if_section_description_redirects_to_section_summary(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-4/optional2",
            data={
                "optional2": True
            })

        assert res.status_code == 302
        self.data_api_client.update_brief.assert_called_with(
            '1234',
            {"optional2": True},
            page_questions=['optional2'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4'
        ) is True

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_post_update_if_single_question_no_description_redirects_to_overview(self, content_loader):
        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-2/required2",
            data={
                "required2": True
            })

        assert res.status_code == 302
        self.data_api_client.update_brief.assert_called_with(
            '1234',
            {"required2": True},
            page_questions=['required2'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
        ) is True

    def test_404_if_brief_does_not_belong_to_user(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    def test_404_if_lot_does_not_allow_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    def test_404_if_lot_does_not_exist(self):
        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-octopuses/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    @pytest.mark.parametrize('framework_status', ['coming', 'open', 'pending', 'standstill', 'expired'])
    def test_404_if_framework_status_is_not_live(self, framework_status):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status=framework_status,
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    def test_404_if_brief_is_already_live(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    def test_404_if_question_does_not_exist(self):
        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/some-made-up-question",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called


class TestPublishBrief(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_brief.return_value = api_stubs.brief()
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        self.login_as_buyer()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_publish_brief(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'numberOfSuppliers': 5,
            'location': 'somewhere',
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address',
            'requirementsLength': '1 week'
        })
        self.data_api_client.get_brief.return_value = brief_json

        res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                               "digital-specialists/1234/publish")
        assert res.status_code == 302
        assert self.data_api_client.publish_brief.called
        assert res.location == "http://localhost/buyers/frameworks/digital-outcomes-and-specialists/" \
                               "requirements/digital-specialists/1234?published=true"

    def test_publish_brief_with_unanswered_required_questions(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(status="draft")

        res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                               "digital-specialists/1234/publish")
        assert res.status_code == 400
        assert not self.data_api_client.publish_brief.called

    def test_404_if_brief_does_not_belong_to_user(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    def test_404_if_brief_has_wrong_lot(self):
        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-outcomes/1234/edit/your-organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 404
        assert not self.data_api_client.update_brief.called

    def test_404_if_framework_status_is_not_live(self):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )

            brief_json = api_stubs.brief(status="draft")
            brief_questions = brief_json['briefs']
            brief_questions.update({
                'backgroundInformation': 'test background info',
                'contractLength': 'A very long time',
                'culturalFitCriteria': ['CULTURAL', 'FIT'],
                'culturalWeighting': 10,
                'essentialRequirements': 'Everything',
                'evaluationType': ['test evaluation type'],
                'existingTeam': 'team team team',
                'importantDates': 'Near future',
                'numberOfSuppliers': 5,
                'location': 'somewhere',
                'organisation': 'test organisation',
                'priceWeighting': 80,
                'specialistRole': 'communicationsManager',
                'specialistWork': 'work work work',
                'startDate': 'startDate',
                'summary': 'blah',
                'technicalWeighting': 10,
                'workingArrangements': 'arrangements',
                'workplaceAddress': 'address',
                'requirementsLength': '1 week'
            })
            self.data_api_client.get_brief.return_value = brief_json

            res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                                   "digital-specialists/1234/publish")
            assert res.status_code == 404
            assert not self.data_api_client.publish_brief.called

    def test_publish_button_available_if_questions_answered(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'location': 'somewhere',
            'numberOfSuppliers': 3,
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address',
            'requirementsLength': '1 week'
        })
        self.data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Publish requirements' in page_html, page_html

    def test_publish_button_unavailable_if_questions_not_answered(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '1 week'
        })
        self.data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Publish requirements' not in page_html

    def test_warning_about_setting_requirement_length_is_not_displayed_if_not_specialist_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )

        self.data_api_client.get_brief.return_value = api_stubs.brief(status="draft", lot_slug="digital-outcomes")

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-outcomes/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 2 weeks' in page_html

    def test_correct_content_is_displayed_if_no_requirementLength_is_set(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(status="draft")

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/set-how-long-your-requirements-will-be-open-for/requirementsLength"' in page_html  # noqa
        assert 'This will show you what the supplier application deadline will be' in page_html
        assert 'Your requirements will be open for' not in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_1_week(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '1 week'
        })
        self.data_api_client.get_brief.return_value = brief_json

        with freeze_time('2016-12-31 23:59:59'):
            res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                                  "digital-specialists/1234/publish")
            page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements will be open for 1 week.' in page_html
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 2 weeks' not in page_html
        assert 'If you publish your requirements today (31 December)' in page_html
        assert 'suppliers will be able to apply until Saturday 7 January 2017 at 11:59pm GMT' in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_2_weeks(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '2 weeks'
        })
        self.data_api_client.get_brief.return_value = brief_json

        with freeze_time('2017-07-17 23:59:59'):
            res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                                  "digital-specialists/1234/publish")
            page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements will be open for 2 weeks.' in page_html
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 1 week' not in page_html
        assert 'If you publish your requirements today (17 July)' in page_html
        assert 'suppliers will be able to apply until Monday 31 July 2017 at 11:59pm GMT' in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_not_set(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': None
        })
        self.data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)
        document = html.fromstring(page_html)

        assert res.status_code == 200
        assert 'Your requirements will be open for 2 weeks.' not in page_html
        assert 'This will show you what the supplier application deadline will be' in page_html
        assert 'Your requirements will be open for 1 week' not in page_html
        assert not document.xpath('//a[contains(text(), "Set how long your requirements will be live for")]')

    def test_heading_for_unanswered_questions_not_displayed_if_only_requirements_length_unset(self):
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'location': 'somewhere',
            'numberOfSuppliers': 3,
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address'
        })
        self.data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "You still need to complete the following questions before your requirements " \
            "can be published:" not in page_html


class TestDeleteBriefSubmission(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_brief.return_value = api_stubs.brief()
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        self.login_as_buyer()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_delete_brief_submission(self):
        for framework_status in ['live', 'expired']:
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete"
            )

            assert res.status_code == 302
            assert self.data_api_client.delete_brief.called
            assert res.location == "http://localhost{}".format(self.briefs_dashboard_url)
            self.assert_flashes("Your requirements ‘I need a thing to do a thing’ were deleted")

    def test_404_if_framework_is_not_live_or_expired(self):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete",
            )
            assert res.status_code == 404
            assert not self.data_api_client.delete_brief.called

    def test_cannot_delete_live_brief(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete",
        )

        assert res.status_code == 404
        assert not self.data_api_client.delete_brief.called

    def test_404_if_brief_does_not_belong_to_user(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={"delete_confirmed": True})

        assert res.status_code == 404

    def test_404_if_brief_has_wrong_lot(self):
        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/delete",
            data={"delete_confirmed": True})

        assert res.status_code == 404


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestWithdrawBriefSubmission(BaseApplicationTest):

    @pytest.mark.parametrize('framework_status', ['live', 'expired'])
    def test_withdraw_brief_submission(self, data_api_client, framework_status):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status=framework_status,
            lots=[api_stubs.lot(slug='digital-specialists', allows_brief=True)]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/withdraw",
            data={"withdraw_confirmed": True}
        )

        assert res.status_code == 302
        assert data_api_client.delete_brief.call_args_list == []
        assert res.location == "http://localhost{}".format(self.briefs_dashboard_url)
        self.assert_flashes("You’ve withdrawn your requirements for ‘I need a thing to do a thing’")

    @pytest.mark.parametrize('framework_status', ['coming', 'open', 'pending', 'standstill'])
    def test_404_if_framework_is_not_live_or_expired(self, data_api_client, framework_status):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status=framework_status,
            lots=[api_stubs.lot(slug='digital-specialists', allows_brief=True)]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/withdraw",
            data={"withdraw_confirmed": True}
        )
        assert res.status_code == 404
        assert not data_api_client.delete_brief.called

    @pytest.mark.parametrize('status', ['draft', 'closed', 'awarded', 'cancelled', 'unsuccessful', 'withdrawn'])
    def test_cannot_withdraw_non_live_brief(self, data_api_client, status):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[api_stubs.lot(slug='digital-specialists', allows_brief=True)]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status=status)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/withdraw",
            data={"withdraw_confirmed": True}
        )

        assert res.status_code == 404
        assert data_api_client.delete_brief.call_args_list == []

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[api_stubs.lot(slug='digital-specialists', allows_brief=True)]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234, status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/withdraw",
            data={"withdraw_confirmed": True}
        )

        assert res.status_code == 404

    def test_404_if_brief_has_wrong_lot(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/withdraw",
            data={"delete_confirmed": True})

        assert res.status_code == 404


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestBriefSummaryPage(BaseApplicationTest):

    SIDE_LINKS_XPATH = '//div[@class="column-one-third"]//a'
    INSTRUCTION_LINKS_XPATH = '//main[@id="content"]//ul/li/a'

    @staticmethod
    def _get_links(document, xpath, text_only=None):
        if text_only:
            return [e.text_content() for e in document.xpath(xpath)]
        return [
            (e.text_content(), e.get('href')) for e in document.xpath(xpath)
        ]

    @pytest.mark.parametrize('framework_status', ['live', 'expired'])
    def test_show_draft_brief_summary_page(self, data_api_client, framework_status):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="draft")
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert self._get_links(document, self.INSTRUCTION_LINKS_XPATH, text_only=True) == [
                'Title',
                'Specialist role',
                'Location',
                'Description of work',
                'Shortlist and evaluation process',
                'Set how long your requirements will be open for',
                'Describe question and answer session',
                'Review and publish your requirements',
                'How to answer supplier questions',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'Download the Digital Outcomes and Specialists contract',
            ]

            assert "Awarded to " not in page_html
            assert 'Are you sure you want to delete these requirements?' not in page_html  # Delete banner hidden
            assert self._get_links(document, self.SIDE_LINKS_XPATH) == [
                (
                    "Delete draft requirements",
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234?delete_requested=True"  # noqa
                )
            ]

    @pytest.mark.parametrize(
        'status, banner_displayed',
        [
            ('draft', True),
            ('live', False), ('closed', False), ('awarded', False), ('cancelled', False), ('unsuccessful', False)
        ]
    )
    def test_brief_summary_with_delete_requested_displays_confirmation_banner_for_draft_briefs_only(
            self, data_api_client, status, banner_displayed
    ):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[api_stubs.lot(slug='digital-specialists', allows_brief=True)]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(status=status)

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234?delete_requested=True"  # noqa
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            assert ('Are you sure you want to delete these requirements?' in page_html) == banner_displayed

    @pytest.mark.parametrize('framework_status', ['live', 'expired'])
    def test_show_live_brief_summary_page_for_live_and_expired_framework(self, data_api_client, framework_status):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="live")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert self._get_links(document, self.INSTRUCTION_LINKS_XPATH, text_only=True) == [
                'View question and answer dates',
                'View your published requirements',
                'Publish questions and answers',
                'How to answer supplier questions',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'Download the Digital Outcomes and Specialists contract',
            ]

            assert "Awarded to " not in page_html
            assert 'Are you sure you want to withdraw these requirements?' not in page_html  # Withdraw banner hidden
            assert self._get_links(document, self.SIDE_LINKS_XPATH) == [
                (
                    'Withdraw requirements',
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234?withdraw_requested=True"  # noqa
                )
            ]

    @pytest.mark.parametrize(
        'status, banner_displayed',
        [
            ('live', True),
            ('draft', False), ('closed', False), ('awarded', False), ('cancelled', False), ('unsuccessful', False)
        ]
    )
    def test_brief_summary_with_withdraw_requested_displays_confirmation_banner_for_live_briefs_only(
            self, data_api_client, status, banner_displayed
    ):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[api_stubs.lot(slug='digital-specialists', allows_brief=True)]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(status=status)

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234?withdraw_requested=True"  # noqa
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            assert ('Are you sure you want to withdraw these requirements?' in page_html) == banner_displayed

    @pytest.mark.parametrize('framework_status', ['live', 'expired'])
    def test_show_closed_brief_summary_page_for_live_and_expired_framework(self, data_api_client, framework_status):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="closed")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert self._get_links(document, self.INSTRUCTION_LINKS_XPATH, text_only=True) == [
                'View your published requirements',
                'View and shortlist suppliers',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'Download the Digital Outcomes and Specialists contract',
                'Let suppliers know the outcome'
            ]

            assert "Awarded to " not in page_html
            assert self._get_links(document, self.SIDE_LINKS_XPATH) == [
                (
                    'Cancel requirements',
                    '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/cancel'
                )
            ]

    @pytest.mark.parametrize('framework_status', ['live', 'expired'])
    @pytest.mark.parametrize(
        'status,award_description',
        [('cancelled', 'the requirements were cancelled'), ('unsuccessful', 'no suitable suppliers applied')]
    )
    def test_show_cancelled_and_unsuccessful_brief_summary_page_for_live_and_expired_framework(
            self, data_api_client, status, award_description, framework_status):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status=status)
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert self._get_links(document, self.INSTRUCTION_LINKS_XPATH, text_only=True) == [
                'View your published requirements',
                'View suppliers who applied',
            ]
            assert "The contract was not awarded - {}.".format(award_description) in page_html

            assert "Awarded to " not in page_html
            assert self._get_links(document, self.SIDE_LINKS_XPATH) == []

    @pytest.mark.parametrize('framework_status', ['live', 'expired'])
    def test_show_awarded_brief_summary_page_for_live_and_expired_framework(self, data_api_client, framework_status):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="awarded")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            brief_json['briefs']['awardedBriefResponseId'] = 999
            data_api_client.get_brief.return_value = brief_json

            data_api_client.get_brief_response.return_value = {
                "briefResponses": {
                    "awardDetails": {
                        "awardedContractStartDate": "2016-4-4",
                        "awardedContractValue": "100"
                    },
                    "id": 213,
                    "status": "awarded",
                    "supplierName": "100 Percent IT Ltd",
                }
            }

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200

            assert data_api_client.get_brief_response.call_args_list == [
                mock.call(999)
            ]

            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert self._get_links(document, self.INSTRUCTION_LINKS_XPATH, text_only=True) == [
                'View your published requirements',
                'View suppliers who applied',
            ]
            assert "Awarded to 100 Percent IT Ltd" in page_html
            assert self._get_links(document, self.SIDE_LINKS_XPATH) == []

    def test_404_if_framework_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 404

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 404

    def test_404_if_brief_has_wrong_lot(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234"
            )

            assert res.status_code == 404

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_links_to_sections_go_to_the_correct_pages_whether_they_be_sections_or_questions(self, content_loader, data_api_client):  # noqa
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            content_fixture = ContentLoader('tests/fixtures/content')
            content_fixture.load_manifest('dos', 'data', 'edit_brief')
            content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200

            document = html.fromstring(res.get_data(as_text=True))
            section_steps = document.xpath(
                '//*[@id="content"]/div/div/ol[contains(@class, "instruction-list")]')
            section_1_link = section_steps[0].xpath('li//a[contains(text(), "Section 1")]')
            section_2_link = section_steps[0].xpath('li//a[contains(text(), "Section 2")]')
            section_4_link = section_steps[0].xpath('li//a[contains(text(), "Section 4")]')

            # section with multiple questions
            assert section_1_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1'
            # section with single question
            assert section_2_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/section-2/required2'  # noqa
            # section with single question and a description
            assert section_4_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4'


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestViewBriefSectionSummaryPage(BaseApplicationTest):

    @mock.patch('app.main.views.buyers.content_loader', autospec=True)
    def test_get_view_section_summary(self, content_loader, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            content_fixture = ContentLoader('tests/fixtures/content')
            content_fixture.load_manifest('dos', 'data', 'edit_brief')
            content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1"
            )

            assert res.status_code == 200

    def test_wrong_lot_get_view_section_summary(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/section-1"
            )

            assert res.status_code == 404


class AbstractViewBriefResponsesPage(BaseApplicationTest):
    def setup_method(self, method):
        super(AbstractViewBriefResponsesPage, self).setup_method(method)

        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )

        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='closed')
        brief_stub['briefs'].update({'publishedAt': self.brief_publishing_date})
        self.data_api_client.get_brief.return_value = brief_stub

        self.data_api_client.find_brief_responses.return_value = self.brief_responses

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super(AbstractViewBriefResponsesPage, self).teardown_method(method)

    def test_page_shows_correct_content_when_eligible_responses(self):
        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "Shortlist suppliers" in page
        assert "2 suppliers" in page
        assert "responded to your requirements and meet all your essential skills and experience." in page
        assert (
            "Any suppliers that did not meet all your essential requirements "
            "have already been told they were unsuccessful."
        ) in page

    @pytest.mark.parametrize('status', buyers.CLOSED_PUBLISHED_BRIEF_STATUSES)
    def test_page_visible_for_awarded_cancelled_unsuccessful_briefs(self, status):
        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='closed')
        brief_stub['briefs'].update(
            {
                'publishedAt': self.brief_publishing_date,
                'status': status
            }
        )
        if status == 'awarded':
            brief_stub['briefs']['awardedBriefResponseId'] = 999

        self.data_api_client.get_brief.return_value = brief_stub
        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        assert res.status_code == 200

    def test_page_does_not_pluralise_for_single_response(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": [self.brief_responses["briefResponses"][0]]
        }

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)
        assert res.status_code == 200
        assert "1 supplier" in page
        assert "responded to your requirements and meets all your essential skills and experience." in page

    def test_404_if_brief_does_not_belong_to_buyer(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", user_id=234)

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404

    def test_404_if_brief_is_not_closed_or_awarded(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", status='live')

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404

    def test_404_if_lot_does_not_allow_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=False),
            ]
        )

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404

    def test_404_if_brief_has_wrong_lot(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404


class TestViewBriefResponsesPageForLegacyBrief(AbstractViewBriefResponsesPage):
    brief_responses = {
        "briefResponses": [
            {"essentialRequirements": [True, True, True, True, True]},
            {"essentialRequirements": [True, False, True, True, True]},
            {"essentialRequirements": [True, True, False, False, True]},
            {"essentialRequirements": [True, True, True, True, True]},
            {"essentialRequirements": [True, True, True, True, False]},
        ]
    }

    brief_publishing_date = '2016-01-21T12:00:00.000000Z'

    def test_page_shows_correct_message_for_legacy_brief_if_no_eligible_responses(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": [self.brief_responses["briefResponses"][1]]
        }

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "There were no applications" in page
        assert "No suppliers met your essential skills and experience requirements." in page
        assert "All the suppliers who applied have already been told they were unsuccessful." in page

    def test_page_shows_csv_download_link(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", status='closed')

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        document = html.fromstring(res.get_data(as_text=True))
        csv_link = document.xpath(
            '//a[@href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses/download"]'  # noqa
        )[0]

        assert res.status_code == 200
        assert self._strip_whitespace(csv_link.text_content()) == \
            "CSVdocument:Downloadsupplierresponsesto‘Ineedathingtodoathing’"


class TestViewBriefResponsesPageForNewFlowBrief(AbstractViewBriefResponsesPage):
    brief_responses = {
        "briefResponses": [
            {"essentialRequirementsMet": True, "essentialRequirements": [{"evidence": "blah"}]},
            {"essentialRequirementsMet": True, "essentialRequirements": [{"evidence": "blah"}]},
        ]
    }

    brief_publishing_date = '2017-01-21T12:00:00.000000Z'

    def test_page_shows_correct_message_for_no_responses(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": []
        }

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "There were no applications" in page
        assert "No suppliers met your essential skills and experience requirements." in page
        assert "All the suppliers who applied have already been told they were unsuccessful." not in page

    def test_page_shows_ods_download_link(self):
        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='closed')
        brief_stub['briefs'].update({'publishedAt': self.brief_publishing_date})
        self.data_api_client.get_brief.return_value = brief_stub

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        document = html.fromstring(res.get_data(as_text=True))
        csv_link = document.xpath(
            '//a[@href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses/download"]'  # noqa
        )[0]

        assert res.status_code == 200
        assert self._strip_whitespace(csv_link.text_content()) == \
            "ODSdocument:Downloadsupplierresponsestothisrequirement"


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestViewQuestionAndAnswerDates(BaseApplicationTest):
    def test_show_question_and_answer_dates_for_published_brief(self, data_api_client):
        for framework_status in ['live', 'expired']:
            with self.app.app_context():
                self.login_as_buyer()
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live")
                brief_json['briefs']['requirementsLength'] = '2 weeks'
                brief_json['briefs']['publishedAt'] = u"2016-04-02T20:10:00.00000Z"
                brief_json['briefs']['clarificationQuestionsClosedAt'] = u"2016-04-12T23:59:00.00000Z"
                brief_json['briefs']['clarificationQuestionsPublishedBy'] = u"2016-04-14T23:59:00.00000Z"
                brief_json['briefs']['applicationsClosedAt'] = u"2016-04-16T23:59:00.00000Z"
                brief_json['briefs']['specialistRole'] = 'communicationsManager'
                brief_json['briefs']["clarificationQuestionsAreClosed"] = True
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                document = html.fromstring(page_html)

                assert (document.xpath('//h1')[0]).text_content().strip() == "Question and answer dates"
                assert all(
                    date in
                    [e.text_content() for e in document.xpath('//main[@id="content"]//th/span')]
                    for date in ['2 April', '8 April', '15 April', '16 April']
                )

    def test_404_if_framework_is_not_live_or_expired(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            with self.app.app_context():
                self.login_as_buyer()
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live")
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
                )

                assert res.status_code == 404

    def test_do_not_show_question_and_answer_dates_for_draft_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="draft")
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 404

    def test_do_not_show_question_and_answer_dates_for_closed_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="closed")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 404


class TestBuyerAccountOverview(BaseApplicationTest):

    def setup_method(self, method):
        super(TestBuyerAccountOverview, self).setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

    def test_buyer_account_overview_page_renders(self):
        self.data_api_client.find_briefs.return_value = find_briefs_mock()
        self.data_api_client.find_direct_award_projects.return_value = {"projects": []}
        self.login_as_buyer()
        res = self.client.get('/buyers')
        assert res.status_code == 200
        assert 'Cloud hosting, software and support' in res.get_data(as_text=True)
        assert 'Digital outcomes, specialists and user research' in res.get_data(as_text=True)

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super(TestBuyerAccountOverview, self).teardown_method(method)
