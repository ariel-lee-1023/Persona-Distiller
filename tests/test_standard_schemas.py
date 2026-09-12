import copy
import json
from pathlib import Path
import sys
import unittest
from jsonschema import Draft202012Validator, ValidationError
from test_recognition import plan_fixture, judge_fixture
import test_recognition
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from score_elements import score_elements
from test_score_elements import procedure

SCHEMAS = Path(__file__).resolve().parents[1] / 'references/schemas'


class StandardSchemaTests(unittest.TestCase):
    def validator(self, name):
        return Draft202012Validator(json.loads((SCHEMAS / name).read_text()))

    def test_all_schemas_are_valid_and_plan_rejects_missing_limits(self):
        for p in SCHEMAS.glob('*.json'): Draft202012Validator.check_schema(json.loads(p.read_text()))
        plan = plan_fixture(); self.validator('recognition-plan.schema.json').validate(plan)
        del plan['generation']['timeout_seconds']
        with self.assertRaises(ValidationError): self.validator('recognition-plan.schema.json').validate(plan)

    def test_evidence_and_judge_contracts(self):
        plan = plan_fixture()
        self.validator('evidence.schema.json').validate({'schema_version': 1, 'records': plan['evidence']})
        cases = [{'id': str(i), 'answers': {'A': 'Inspect evidence first.', 'B': 'Review the report.'}} for i in range(3)]
        judge = judge_fixture(cases, 0)
        self.validator('recognition-judge.schema.json').validate(judge)
        del judge['cases'][0]['A']['reasoning']['passage']
        with self.assertRaises(ValidationError): self.validator('recognition-judge.schema.json').validate(judge)

    def test_pending_conflicting_research_records_validate_without_invented_resolution(self):
        a, b = procedure('a'), procedure('b'); a['conflicts_with'] = ['b']
        result = score_elements({'elements': [a, b]})
        result['input_hash'] = 'sha256:' + '0' * 64
        self.validator('scores.schema.json').validate(result)
        self.assertEqual(result['retained'], [])

    def test_completion_artifact_validates(self):
        fixture = test_recognition.RunnerTests('test_full_first_adoption_eight_calls_blinding_caps_and_resume')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.execute()
        self.validator('validation.schema.json').validate(fixture.completion())


if __name__ == '__main__': unittest.main()
