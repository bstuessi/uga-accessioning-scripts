"""Tests error handling for a missing or incorrect script argument.
Error handling is in the main body of the script, so the tests run the entire script."""

import os
import subprocess
import unittest


class MyTestCase(unittest.TestCase):

    def test_no_argument_error(self):
        """Runs format_analysis.py without an argument.
         Result for testing is the error message."""
        script_path = os.path.join('..', 'format_analysis.py')
        script_output = subprocess.run(f'python {script_path}', shell=True, stdout=subprocess.PIPE)

        result = script_output.stdout.decode("utf-8")
        expected = '\r\nThe required script argument (accession_folder) is missing.\r\n'

        self.assertEqual(result, expected, 'Problem with no argument error')

    def test_path_error(self):
        """Runs format_analysis.py with an argument that isn't a valid path.
         Result for testing is the error message."""
        script_path = os.path.join('..', 'format_analysis.py')
        script_output = subprocess.run(f"python {script_path} C:/User/Wrong/Path", shell=True, stdout=subprocess.PIPE)

        result = script_output.stdout.decode("utf-8")
        expected = "\r\nThe provided accession folder 'C:/User/Wrong/Path' is not a valid directory.\r\n"

        self.assertEqual(result, expected, 'Problem with path error')


if __name__ == '__main__':
    unittest.main()
