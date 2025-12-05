import unittest

import prompts


class TestPrompts(unittest.TestCase):
    def setUp(self):
        # patcha a função get_schema_from_db usada em prompts
        self._orig = getattr(prompts, 'get_schema_from_db', None)
        prompts.get_schema_from_db = lambda path: "CREATE TABLE students(id INTEGER PRIMARY KEY, name TEXT);"

    def tearDown(self):
        if self._orig is None:
            delattr(prompts, 'get_schema_from_db')
        else:
            prompts.get_schema_from_db = self._orig

    def test_criar_prompt_basico_contains_schema_and_question(self):
        prompt = prompts.criar_prompt_basico('How many students?', 'college_3')
        self.assertIn('How many students?', prompt)
        self.assertIn('CREATE TABLE students', prompt)
        self.assertIn('SQL Query:', prompt)

    def test_criar_prompt_few_shot_includes_examples(self):
        exemplos = [{'question': 'Q1', 'query': 'SELECT 1;'}]
        prompt = prompts.criar_prompt_few_shot('How many students?', 'college_3', exemplos=exemplos)
        self.assertIn('Q1', prompt)
        self.assertIn('SELECT 1', prompt)
        self.assertIn('How many students?', prompt)


if __name__ == '__main__':
    unittest.main()
