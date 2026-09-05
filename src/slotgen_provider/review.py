import hashlib
import json
from pathlib import Path


class IncompleteReview(ValueError):
    pass


def response_text(response):
    try:
        choice = response['choices'][0]
        message = choice['message']
    except (KeyError, IndexError, TypeError) as error:
        raise IncompleteReview('Malformed provider response') from error
    if choice.get('finish_reason') != 'stop' or message.get('refusal'):
        raise IncompleteReview('Provider response did not finish normally')
    content = message.get('content')
    if isinstance(content, list):
        content = ''.join(item.get('text', '') for item in content if item.get('type') == 'text')
    if not isinstance(content, str) or not content.strip():
        raise IncompleteReview('Provider returned no review text')
    return content


def parse_review_response(response):
    try:
        result = json.loads(response_text(response))
    except json.JSONDecodeError as error:
        raise IncompleteReview('Expected structured review JSON') from error
    if not isinstance(result, dict) or result.get('verdict') not in ('ACCEPT', 'REVISE', 'REJECT', 'INCOMPLETE'):
        raise IncompleteReview('Missing review verdict')
    if not isinstance(result.get('issues'), list) or not isinstance(result.get('coverage'), str) or not result['coverage'].strip():
        raise IncompleteReview('Review must include issues and coverage')
    if result['verdict'] == 'ACCEPT' and result['issues']:
        raise IncompleteReview('ACCEPT conflicts with unresolved issues')
    return result


def input_fingerprints(files):
    return [{'name': Path(file).name, 'sha256': hashlib.sha256(Path(file).read_bytes()).hexdigest()} for file in files]
