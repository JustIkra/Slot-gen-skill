import unittest
from slotgen_provider.review import IncompleteReview, parse_review_response, response_text


def response(content, reason='stop'):
    return {'choices': [{'finish_reason': reason, 'message': {'content': content}}]}


class ReviewTests(unittest.TestCase):
    def test_truncated_text_cannot_be_an_accepted_audit(self):
        with self.assertRaises(IncompleteReview):
            response_text(response('ACCEPT', 'length'))

    def test_empty_refused_and_unstructured_audits_fail(self):
        for content in ['', 'looks good', '{"verdict":"ACCEPT"}']:
            with self.subTest(content=content), self.assertRaises(IncompleteReview):
                parse_review_response(response(content))

    def test_valid_audit_preserves_issues_and_coverage(self):
        result = parse_review_response(response('{"verdict":"REVISE","issues":["rim clipping"],"coverage":"full frame"}'))
        self.assertEqual(result['verdict'], 'REVISE')
        self.assertEqual(result['issues'], ['rim clipping'])
