import os
import json
from mock import Mock
from dmcontent.content_loader import ContentLoader
from werkzeug.datastructures import MultiDict

from app.main.presenters.search_presenters import filters_for_lot, set_filter_states


content_loader = ContentLoader('tests/fixtures/content')
content_loader.load_manifest('g6', 'data', 'manifest')
questions_builder = content_loader.get_builder('g6', 'manifest')


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_fixture_multiple_pages_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_multiple_pages_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestSearchFilters(object):

    def _get_filter_group_by_label(self, lot, label):
        filter_groups = filters_for_lot(lot, questions_builder)
        for filter_group in filter_groups:
            if filter_group['label'] == label:
                return filter_group

    def _get_request_for_params(self, params):
        return Mock(args=MultiDict(params))

    def test_get_filter_groups_from_questions_with_radio_filters(self):
        radios_filter_group = self._get_filter_group_by_label(
            'saas', 'Radios example'
        )

        assert radios_filter_group == {
            'label': 'Radios example',
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'radiosExample',
                    'id': 'radiosExample-option-1',
                    'value': 'option 1',
                },
                {
                    'label': 'Option 2',
                    'name': 'radiosExample',
                    'id': 'radiosExample-option-2',
                    'value': 'option 2',
                },
            ],
        }

    def test_get_filter_groups_from_questions_with_checkbox_filters(self):
        checkboxes_filter_group = self._get_filter_group_by_label(
            'saas', 'Checkboxes example'
        )
        assert checkboxes_filter_group == {
            'label': 'Checkboxes example',
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'checkboxesExample',
                    'id': 'checkboxesExample-option-1',
                    'value': 'option 1',
                },
                {
                    'label': 'Option 2',
                    'name': 'checkboxesExample',
                    'id': 'checkboxesExample-option-2',
                    'value': 'option 2',
                },
            ],
        }

    def test_get_filter_groups_from_questions_with_boolean_filters(self):
        booleans_filter_group = self._get_filter_group_by_label(
            'saas', 'Booleans example'
        )
        assert booleans_filter_group == {
            'label': 'Booleans example',
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                },
                {
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                },
            ],
        }

    def test_request_filters_are_set(self):
        search_filters = filters_for_lot('saas', questions_builder)
        request = self._get_request_for_params({
            'q': 'email',
            'booleanExample1': 'true'
        })

        set_filter_states(search_filters, request)
        assert search_filters[0]['filters'][0]['name'] == 'booleanExample1'
        assert search_filters[0]['filters'][0]['checked'] is True
        assert search_filters[0]['filters'][1]['name'] == 'booleanExample2'
        assert search_filters[0]['filters'][1]['checked'] is False

    def test_filter_groups_have_correct_default_state(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas'
        })

        search_filters = filters_for_lot('paas', questions_builder)
        set_filter_states(search_filters, request)
        assert search_filters[0] == {
            'label': 'Booleans example',
            'filters': [
                {
                    'checked': False,
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                },
                {
                    'checked': False,
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                },
            ],
        }

    def test_filter_groups_have_correct_state_when_changed(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas',
            'booleanExample1': 'true'
        })

        search_filters = filters_for_lot('paas', questions_builder)
        set_filter_states(search_filters, request)

        assert search_filters[0] == {
            'label': 'Booleans example',
            'filters': [
                {
                    'checked': True,
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                },
                {
                    'checked': False,
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                },
            ],
        }

    def test_no_lot_is_the_same_as_all(self):
        all_filters = self._get_filter_group_by_label(
            'all', 'Radios example'
        )
        no_lot_filters = self._get_filter_group_by_label(
            None, 'Radios example'
        )

        assert all_filters
        assert all_filters == no_lot_filters

    def test_instance_has_correct_filter_groups_for_paas(self):
        search_filters = filters_for_lot('paas', questions_builder)

        filter_group_labels = [
            group['label'] for group in search_filters
        ]

        assert 'Booleans example' in filter_group_labels
        assert 'Checkboxes example' in filter_group_labels
        assert 'Radios example' in filter_group_labels

    def test_instance_has_correct_filter_groups_for_iaas(self):
        search_filters = filters_for_lot('iaas', questions_builder)

        filter_group_labels = [
            group['label'] for group in search_filters
        ]

        assert 'Booleans example' not in filter_group_labels
        assert 'Checkboxes example' in filter_group_labels
        assert 'Radios example' in filter_group_labels