"""Tests the command for making FITS files when there is not already a folder of FITs XML from a previous script
iteration, including error handling for  FITS when it is in a different directory letter than the accession."""

import os
import pandas as pd
import shutil
import subprocess
import unittest
import configuration as c


class MyTestCase(unittest.TestCase):

    def setUp(self):
        """
        Makes an accession folder for testing. Includes a folder and files.
        """
        os.makedirs(os.path.join('accession', 'folder'))
        for file_path in ('file.txt', 'folder\\file.txt', 'folder\\other.txt'):
            with open(f'accession\\{file_path}', 'w') as file:
                file.write('Text')

    def tearDown(self):
        """
        Deletes the initial test accession folder and the FITS folder produced during testing.
        """
        shutil.rmtree('accession')
        shutil.rmtree('accession_FITS')

    def test_make_fits(self):
        """
        Test for correctly making new FITS files.
        Result for testing is the contents of the FITS folder.
        """
        accession_folder = os.path.join(os.getcwd(), 'accession')

        # Runs the code being tested.
        # Expect the "else" branch to run. The "if" branch calls update_fits() in the main script.
        # Does not include printing messages to the terminal or existing after an error that are in the main script.
        fits_output = os.path.join(os.getcwd(), 'accession_FITS')
        if os.path.exists(fits_output):
            pass
        else:
            os.mkdir(fits_output)
            fits_status = subprocess.run(f'"{c.FITS}" -r -i "{accession_folder}" -o "{fits_output}"',
                                         shell=True, stderr=subprocess.PIPE)

        # Makes a list with the files that are actually in the accession_fits folder after running the test.
        results = []
        for file in os.listdir('accession_FITS'):
            results.append(file)

        # Makes a list with the files that should be in the accession_FITS folder.
        expected = ['file.txt-1.fits.xml', 'file.txt.fits.xml', 'other.txt.fits.xml']

        # Compares the results. assertEqual prints "OK" or the differences between the two lists.
        self.assertEqual(results, expected, 'Problem with make fits')

    def test_fits_class_error(self):
        """
        Test for error handling when FITS is in a different directory letter than the accession folder.
        Result for testing is the error message.
        """

        # In format_analysis.py, the FITS path is taken from the configuration.py file.
        fits_diff_path = 'X:\\test\\fits.bat'
        accession_folder = os.path.join(os.getcwd(), 'accession')

        # Runs the code being tested.
        # Expect the "else" branch to run. The "if" branch calls update_fits() in the main script.
        # Does not include printing messages to the terminal or existing after an error that are in the main script.
        fits_output = os.path.join(os.getcwd(), 'accession_FITS')
        if os.path.exists(fits_output):
            pass
        else:
            os.mkdir(fits_output)
            fits_status = subprocess.run(f'"{fits_diff_path}" -r -i "{accession_folder}" -o "{fits_output}"',
                                         shell=True, stderr=subprocess.PIPE)

        # Compares the error message generated by the script to the expected value.
        result = fits_status.stderr.decode('utf-8')
        expected = 'Error: Could not find or load main class edu.harvard.hul.ois.fits.Fits\r\n'
        self.assertEqual(result, expected, 'Problem with fits class error')


if __name__ == '__main__':
    unittest.main()
