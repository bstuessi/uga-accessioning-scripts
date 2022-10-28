"""Purpose: tests each function and analysis component (each subset and subtotal) in the format_analysis.py script.
Each test creates simplified input, runs the code, and compares it to the expected output.
Tests include all data variation observed to date and error handling.
Results for failed tests are saved to a directory specified with the script argument.

For any tests that do not use a function from format_analysis.py, check the code is up to date before running the test.
If the input for any function or analysis changes, edit the test input and expected results."""

# usage: python path/format_analysis_tests.py path/output_folder

import gzip
import io
import shutil

from format_analysis_functions import *


def compare_strings(test_name, actual, expected):
    """Compares two strings, one with the actual script output and one with the expected values.
    Prints if they match (test passes) or not (test fails) and updates the counter.
    Results for failed tests are saved to a text file in the output folder for review."""

    # Test that passes. Prints the result and updates the counter.
    if actual == expected:
        print("Pass: ", test_name)
        global PASSED_TESTS
        PASSED_TESTS += 1

    # Test that fails.
    else:
        # Prints the result and updates the counter.
        print("FAIL: ", test_name)
        global FAILED_TESTS
        FAILED_TESTS += 1

        # Saves a log to the output folder.
        with open(f"{test_name}_comparison_results.txt", "w") as file:
            file.write("Test output:\n")
            file.write(actual)
            file.write("\n\nExpected output:\n")
            file.write(expected)


def compare_dataframes(test_name, df_actual, df_expected):
    """Compares two dataframes, one with the actual script output and one with the expected values.
    Prints if they match (test passes) or not (test fails) and updates the counter.
    Results for failed tests are saved to a CSV in the output folder for review."""

    # Makes a new dataframe that merges the values of the two dataframes.
    df_comparison = df_actual.merge(df_expected, indicator=True, how="outer")

    # Makes a dataframe with just the errors (merge value isn't both).
    df_errors = df_comparison[df_comparison["_merge"] != "both"]

    # If the merged dataframe is empty (everything matched), prints that the test passes.
    # Otherwise, saves the dataframe with the complete merge (including matches) to a CSV in the output directory.
    if len(df_errors) == 0:
        print("Pass: ", test_name)
        global PASSED_TESTS
        PASSED_TESTS += 1
    else:
        print("FAIL: ", test_name)
        global FAILED_TESTS
        FAILED_TESTS += 1
        df_comparison.to_csv(f"{test_name}_comparison_results.csv", index=False)


def test_argument(repo_path):
    """Tests error handling for a missing or incorrect script argument."""

    # Calculates the path to the format_analysis.py script so this function can run it.
    script_path = os.path.join(repo_path, "format_analysis.py")

    # TEST ONE: Runs format_analysis.py without an argument and verifies the correct error message is made.
    no_argument = subprocess.run(f"python {script_path}", shell=True, stdout=subprocess.PIPE)
    error_msg = "\r\nThe required script argument (accession_folder) is missing.\r\n"
    compare_strings("Argument_Missing", no_argument.stdout.decode("utf-8"), error_msg)

    # TEST TWO: Runs format_analysis.py with an argument that isn't a valid path and
    # verifies the correct error message is made.
    wrong_argument = subprocess.run(f"python {script_path} C:/User/Wrong/Path", shell=True, stdout=subprocess.PIPE)
    error_msg = "\r\nThe provided accession folder 'C:/User/Wrong/Path' is not a valid directory.\r\n"
    compare_strings("Argument_Invalid_Path", wrong_argument.stdout.decode("utf-8"), error_msg)


def test_check_configuration_function(repo_path):
    """Tests error handling from a missing configuration file, missing variables, and variables with invalid paths."""

    # Renames the current configuration file so errors can be generated without losing the correct file.
    os.rename(f"{repo_path}/configuration.py", f"{repo_path}/configuration_original.py")

    # TEST ONE: Runs the script with no configuration.py present and verifies the correct error message is made.
    no_config = subprocess.run(f"python {repo_path}/format_analysis.py {os.getcwd()}",
                               shell=True, stdout=subprocess.PIPE)
    error_msg = "\r\nCould not run the script. Missing the required configuration.py file." \
                "\r\nMake a configuration.py file using configuration_template.py and save it to the folder with the script.\r\n"
    compare_strings("Configuration_File_Missing", no_config.stdout.decode("utf-8"), error_msg)

    # TEST TWO: Makes a configuration file without any of the required variables.
    # Runs the script and verifies the correct error message is made.
    # Deletes the configuration file after the test is complete.
    with open(f"{repo_path}/configuration.py", "w") as config:
        config.write('# Constants used for other scripts\nvariable = "value"\n')
    no_var = subprocess.run(f"python {repo_path}/format_analysis.py {os.getcwd()}", shell=True, stdout=subprocess.PIPE)
    error_msg = '\r\nProblems detected with configuration.py:\r\n' \
                '   * FITS variable is missing from the configuration file.\r\n' \
                '   * ITA variable is missing from the configuration file.\r\n' \
                '   * RISK variable is missing from the configuration file.\r\n' \
                '   * NARA variable is missing from the configuration file.\r\n\r\n' \
                'Correct the configuration file, using configuration_template.py as a model.\r\n'
    compare_strings("Configuration_File_Missing_Variables", no_var.stdout.decode("utf-8"), error_msg)
    os.remove(f"{repo_path}/configuration.py")

    # TEST THREE: Makes a configuration file with the required variables but all have incorrect file paths.
    # Runs the script and verifies the correct error message is made.
    # Deletes the configuration file after the test is complete.
    with open(f"{repo_path}/configuration.py", "w") as config:
        config.write('# Constants used for other scripts\n')
        config.write('FITS = "C:/Users/Error/fits.bat"\n')
        config.write('ITA = "C:/Users/Error/ITAfileformats.csv"\n')
        config.write('RISK = "C:/Users/Error/Riskfileformats.csv"\n')
        config.write('NARA = "C:/Users/Error/NARA.csv"\n')
    path_error = subprocess.run(f"python {repo_path}/format_analysis.py {os.getcwd()}", shell=True, stdout=subprocess.PIPE)
    error_msg = "\r\nProblems detected with configuration.py:\r\n" \
                "   * FITS path 'C:/Users/Error/fits.bat' is not correct.\r\n" \
                "   * ITAfileformats.csv path 'C:/Users/Error/ITAfileformats.csv' is not correct.\r\n" \
                "   * Riskfileformats.csv path 'C:/Users/Error/Riskfileformats.csv' is not correct.\r\n" \
                "   * NARA Preservation Action Plans CSV path 'C:/Users/Error/NARA.csv' is not correct.\r\n\r\n" \
                "Correct the configuration file, using configuration_template.py as a model.\r\n"
    compare_strings("Configuration_File_Variable_Paths_Error", path_error.stdout.decode("utf-8"), error_msg)
    os.remove(f"{repo_path}/configuration.py")

    # Renames the original configuration file back to configuration.py.
    os.rename(f"{repo_path}/configuration_original.py", f"{repo_path}/configuration.py")


def test_csv_to_dataframe_function():
    """Tests reading all four CSVs into dataframes and adding prefixes to FITS and NARA dataframes."""

    # Makes a FITS CSV with no special characters to use for testing.
    # In format_analysis.py, this would be made earlier in the script and have more columns.
    # The other CSVs read by this function are already on the local machine and paths are in configuration.py
    with open("accession_fits.csv", "w", newline="") as file:
        file_write = csv.writer(file)
        file_write.writerow(["File_Path", "Format_Name", "Format_Version", "Multiple_IDs"])
        file_write.writerow([r"C:\Coll\accession\CD001_Images\IMG1.JPG", "JPEG EXIF", "1.01", False])
        file_write.writerow([r"C:\Coll\accession\CD002_Website\index.html", "Hypertext Markup Language", "4.01", True])
        file_write.writerow([r"C:\Coll\accession\CD002_Website\index.html", "HTML Transitional", "HTML 4.01", True])

    # RUNS THE FUNCTION BEING TESTED ON ALL FOUR CSVS.
    df_fits = csv_to_dataframe("accession_fits.csv")
    df_ita = csv_to_dataframe(c.ITA)
    df_other = csv_to_dataframe(c.RISK)
    df_nara = csv_to_dataframe(c.NARA)

    # For each CSV, tests the function worked by verifying the column names and that the dataframe isn't empty.
    # Column names are converted to a comma separated string to work with the compare_strings() function.
    # The test can't check the data in the dataframe since it uses the real CSVs, which are updated frequently.
    global FAILED_TESTS
    if len(df_fits) != 0:
        expected = "FITS_File_Path, FITS_Format_Name, FITS_Format_Version, FITS_Multiple_IDs"
        compare_strings("CSV_to_DF_FITS", ', '.join(df_fits.columns.to_list()), expected)
    else:
        print("FAIL: CSV_to_DF FITS dataframe is empty")
        FAILED_TESTS += 1

    if len(df_ita) != 0:
        compare_strings("CSV_to_DF_ITA", ', '.join(df_ita.columns.to_list()), "FITS_FORMAT, NOTES")
    else:
        print("FAIL: CSV_to_DF ITA dataframe is empty")
        FAILED_TESTS += 1

    if len(df_other) != 0:
        compare_strings("CSV_to_DF_Other", ', '.join(df_other.columns.to_list()), "FITS_FORMAT, RISK_CRITERIA")
    else:
        print("FAIL: CSV_to_DF Other dataframe is empty")
        FAILED_TESTS += 1

    if len(df_nara) != 0:
        expected = "NARA_Format Name, NARA_File Extension(s), NARA_Category/Plan(s), NARA_NARA Format ID, " \
                   "NARA_MIME type(s), NARA_Specification/Standard URL, NARA_PRONOM URL, NARA_LOC URL, " \
                   "NARA_British Library URL, NARA_WikiData URL, NARA_ArchiveTeam URL, NARA_ForensicsWiki URL, " \
                   "NARA_Wikipedia URL, NARA_docs.fileformat.com, NARA_Other URL, NARA_Notes, NARA_Risk Level, " \
                   "NARA_Preservation Action, NARA_Proposed Preservation Plan, NARA_Description and Justification, " \
                   "NARA_Preferred Processing and Transformation Tool(s)"
        compare_strings("CSV_to_DF_NARA", ', '.join(df_nara.columns.to_list()), expected)
    else:
        print("FAIL: CSV_to_DF NARA dataframe is empty")
        FAILED_TESTS += 1


def test_csv_to_dataframe_function_encoding_error():
    """Tests unicode error handling when reading a CSV into a dataframe."""

    # Makes a FITS CSV with special characters (copyright symbol and accented e) to use for testing.
    # In format_analysis.py, this would be made earlier in the script and have more columns.
    with open("accession_fits.csv", "w", newline="") as file:
        file_write = csv.writer(file)
        file_write.writerow(["File_Path", "Format_Name", "Format_Version", "Multiple_IDs"])
        file_write.writerow([r"C:\Coll\accession\CD001_Images\©Image.JPG", "JPEG EXIF", "1.01", False])
        file_write.writerow([r"C:\Coll\accession\CD002_Website\indexé.html", "Hypertext Markup Language", "4.01", True])
        file_write.writerow([r"C:\Coll\accession\CD002_Website\indexé.html", "HTML Transitional", "HTML 4.01", True])

    # RUNS THE FUNCTION BEING TESTED.
    # Prevents it from printing a status message to the terminal.
    # In format_analysis.py, it prints a warning for the archivist that the CSV had encoding errors.
    text_trap = io.StringIO()
    sys.stdout = text_trap
    df_fits = csv_to_dataframe("accession_fits.csv")
    sys.stdout = sys.__stdout__

    # Makes a dataframe with the expected values in df_fits after the CSV is read with encoding_errors="ignore".
    # This causes characters to be skipped if they can't be read.
    rows = [[r"C:\Coll\accession\CD001_Images\Image.JPG", "JPEG EXIF", "1.01", False],
            [r"C:\Coll\accession\CD002_Website\index.html", "Hypertext Markup Language", "4.01", True],
            [r"C:\Coll\accession\CD002_Website\index.html", "HTML Transitional", "HTML 4.01", True]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_Multiple_IDs"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the contents of the FITS folder to the expected values.
    compare_dataframes("CSV_to_DF_Encoding", df_fits, df_expected)

    # Deletes the test file.
    os.remove("accession_fits.csv")


def test_make_fits_xml():
    """Tests the command for making FITS files when there is not already a folder of FITs XML
    from a previous script iteration."""

    # Makes an accession folder with files to use for testing.
    accession_folder = fr"{output}\accession"
    os.makedirs(fr"{accession_folder}\folder")
    for file_path in ("file.txt", r"folder\file.txt", r"folder\other.txt"):
        with open(fr"accession\{file_path}", "w") as file:
            file.write("Text")

    # RUNS THE CODE BEING TESTED.
    # Makes the directory for FITS files and calls FITS to make the FITS XML files.
    # In format_analysis.py, this is done in the main body of the script after testing that the folder doesn't exist
    # and also exits the script if there is an error.
    fits_output = f"{output}/accession_FITS"
    os.mkdir(fits_output)
    subprocess.run(f'"{c.FITS}" -r -i "{accession_folder}" -o "{fits_output}"', shell=True, stderr=subprocess.PIPE)

    # Makes a dataframe with the files that should be in the accession_FITS folder.
    df_expected = pd.DataFrame(["file.txt.fits.xml", "file.txt-1.fits.xml", "other.txt.fits.xml"], columns=["Files"])

    # Makes a dataframe with the files that are actually in the accession_fits folder after running the test.
    fits_files = []
    for root, dirs, files in os.walk("accession_fits"):
        fits_files.extend(files)
    df_fits_files = pd.DataFrame(fits_files, columns=["Files"])

    # Compares the contents of the FITS folder to the expected values.
    compare_dataframes("Make_FITS_XML", df_fits_files, df_expected)

    # Deletes the test files.
    shutil.rmtree(fr"{output}\accession")
    shutil.rmtree(fr"{output}\accession_FITS")


def test_fits_class_error():
    """Tests the error handling for FITS when it is in a different directory than the source files.
    For this test to work, the fits.bat file must be in the specified location."""

    # Makes an accession folder with files to use for testing.
    accession_folder = fr"{output}\accession"
    os.mkdir(accession_folder)
    with open(fr"accession\file.txt", "w") as file:
        file.write("Text")

    # Makes a variable with a FITS file path in a different directory from the accession folder.
    # In format_analysis.py, the FITS path is taken from the configuration.py file.
    fits_path = r"X:\test\fits.bat"

    # RUNS THE CODE BEING TESTED.
    # Makes the directory for FITS files and calls FITS to make the FITS XML files.
    # In format_analysis.py, this is done in the main body of the script after testing that the folder doesn't exist.
    fits_output = f"{output}/accession_FITS"
    os.mkdir(fits_output)
    fits_result = subprocess.run(f'"{fits_path}" -r -i "{accession_folder}" -o "{fits_output}"',
                                 shell=True, stderr=subprocess.PIPE)

    # Compares the error message generated by the script to the expected value.
    error_msg = "Error: Could not find or load main class edu.harvard.hul.ois.fits.Fits\r\n"
    compare_strings("FITS_Class_Error", fits_result.stderr.decode("utf-8"), error_msg)

    # Deletes the test files.
    shutil.rmtree(fr"{output}\accession")
    shutil.rmtree(fr"{output}\accession_FITS")


def test_update_fits_function():
    """Tests that the FITS folder is correctly updated when files are deleted from and added to the accession folder."""

    # Makes an accession folder with files.
    accession_folder = fr"{output}\accession"
    os.makedirs(fr"{accession_folder}\dir")
    paths = ["file.txt", "delete.txt", r"dir\delete.txt", r"dir\delete2.txt", r"dir\file.txt", r"dir\spare.txt"]
    for file_path in paths:
        with open(fr"accession\{file_path}", "w") as file:
            file.write("Text")

    # Makes FITS XML for the accession to use for testing.
    # In format_analysis.py, this is done in the main body of the script.
    fits_output = fr"{output}\accession_FITS"
    os.mkdir(fits_output)
    subprocess.run(f'"{c.FITS}" -r -i "{accession_folder}" -o "{fits_output}"', shell=True)

    # Deletes 2 files and adds 1 file to the accession folder.
    os.remove(r"accession\delete.txt")
    os.remove(r"accession\dir\delete2.txt")
    with open(r"accession\new_file.txt", "w") as file:
        file.write("Text")

    # RUNS THE FUNCTION BEING TESTED.
    update_fits(accession_folder, fits_output, output, "accession")

    # Makes a dataframe with the files which should be in the FITs folder.
    expected = ["delete.txt-1.fits.xml", "file.txt.fits.xml", "file.txt-1.fits.xml", "new_file.txt.fits.xml",
                "spare.txt.fits.xml"]
    df_expected = pd.DataFrame(expected, columns=["Files"])

    # Makes a dataframe with the files that are in the FITS folder.
    fits_files = []
    for root, dirs, files in os.walk("accession_fits"):
        fits_files.extend(files)
    df_fits_files = pd.DataFrame(fits_files, columns=["Files"])

    # Compares the contents of the FITS folder to the expected values.
    compare_dataframes("Update_FITS", df_fits_files, df_expected)

    # Deletes the test files.
    shutil.rmtree("accession")
    shutil.rmtree("accession_FITS")


def test_make_fits_csv_function():
    """Tests all known variations for FITS data extraction and reformatting."""

    # Makes an accession folder with files organized into 2 folders.
    # Formats included: csv, gzip, html, plain text, xlsx
    # Variations: one and multiple format ids, with and without optional fields, one or multiple tools,
    #             empty with another format id, file with multiple ids with same name and one has PUID (gzip).
    accession_folder = fr"{output}\accession"
    os.makedirs(fr"{accession_folder}\disk1")
    df_spreadsheet = pd.DataFrame({"C1": ["text"*1000], "C2": ["text"*1000], "C3": ["text"*1000]})
    df_spreadsheet = pd.concat([df_spreadsheet]*500, ignore_index=True)
    df_spreadsheet.to_csv(r"accession\disk1\data.csv", index=False)
    df_spreadsheet.to_excel(r"accession\disk1\data.xlsx", index=False)
    df_spreadsheet["C3"] = "New Text"*10000
    df_spreadsheet.to_csv(r"accession\disk1\data_update.csv", index=False)
    with open(r"accession\disk1\file.txt", "w") as file:
        file.write("Text" * 500)
    os.makedirs(fr"{accession_folder}\disk2")
    with open(r"accession\disk2\file.txt", "w") as file:
        file.write("Text" * 550)
    with open(r"accession\disk2\error.html", "w") as file:
        file.write("<body>This isn't really html</body>")
    open(r"accession\disk2\empty.txt", "w").close()
    with gzip.open(r"accession\disk2\zipping.gz", "wb") as file:
        file.write(b"Test Text\n" * 100000)

    # Makes FITS XML for the accession to use for testing.
    # In format_analysis.py, there is also error handling for if FITS has a load class error.
    fits_output = f"{output}/accession_FITS"
    os.mkdir(fits_output)
    subprocess.run(f'"{c.FITS}" -r -i "{accession_folder}" -o "{fits_output}"', shell=True)

    # RUNS THE FUNCTION BEING TESTED.
    make_fits_csv(fr"{output}\accession_FITS", accession_folder, output, "accession")

    # Makes a dataframe with the expected values.
    # Calculates size for XLSX because the size varies every time it is made.
    today = datetime.date.today().strftime('%Y-%m-%d')
    rows = [[fr"{output}\accession\disk1\data.csv", "Comma-Separated Values (CSV)", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/18", "Droid version 6.4", False, today, 6002.01,
             "f95a4c954014342e4bf03f51fcefaecd", np.NaN, np.NaN, np.NaN, np.NaN],
            [fr"{output}\accession\disk1\data.xlsx", "ZIP Format", 2,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/263",
             "Droid version 6.4; file utility version 5.03; ffident version 0.2", True, today,
             round(os.path.getsize(fr"{output}\accession\disk1\data.xlsx")/1000, 3), "XXXXXXXXXX",
             "Microsoft Excel", np.NaN, np.NaN, np.NaN],
            [fr"{output}\accession\disk1\data.xlsx", "XLSX", np.NaN, np.NaN, "Exiftool version 11.54", True, today,
             round(os.path.getsize(fr"{output}\accession\disk1\data.xlsx")/1000, 3), "XXXXXXXXXX",
             "Microsoft Excel", np.NaN, np.NaN, np.NaN],
            [fr"{output}\accession\disk1\data.xlsx", "Office Open XML Workbook", np.NaN, np.NaN, "Tika version 1.21",
             True, today, round(os.path.getsize(fr"{output}\accession\disk1\data.xlsx")/1000, 3),
             "XXXXXXXXXX", "Microsoft Excel", np.NaN, np.NaN, np.NaN],
            [fr"{output}\accession\disk1\data_update.csv", "Comma-Separated Values (CSV)", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/18", "Droid version 6.4", False, today, 44002.01,
             "d5e857a4bd33d2b5a2f96b78ccffe1f3", np.NaN, np.NaN, np.NaN, np.NaN],
            [fr"{output}\accession\disk2\empty.txt", "empty", np.NaN, np.NaN, "file utility version 5.03", False, today,
             0, "d41d8cd98f00b204e9800998ecf8427e", np.NaN, np.NaN, np.NaN, np.NaN],
            [fr"{output}\accession\disk2\error.html", "Extensible Markup Language", 1, np.NaN, "Jhove version 1.20.1",
             False, today, 0.035, "e080b3394eaeba6b118ed15453e49a34", np.NaN, True, True,
             "Not able to determine type of end of line severity=info"],
            [fr"{output}\accession\disk1\file.txt", "Plain text", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/111",
             "Droid version 6.4; Jhove version 1.20.1; file utility version 5.03", False, today, 2,
             "7b71af3fdf4a2f72a378e3e77815e497", np.NaN, True, True, np.NaN],
            [fr"{output}\accession\disk2\file.txt", "Plain text", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/111",
             "Droid version 6.4; Jhove version 1.20.1; file utility version 5.03", False, today, 2.2,
             "e700d0871d44af1a217f0bf32320f25c", np.NaN, True, True, np.NaN],
            [fr"{output}\accession\disk2\zipping.gz", "GZIP Format", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/266", "Droid version 6.4; Tika version 1.21",
             False, today, 1.993, "XXXXXXXXXX", np.NaN, np.NaN, np.NaN, np.NaN]]
    column_names = ["File_Path", "Format_Name", "Format_Version", "PUID", "Identifying_Tool(s)", "Multiple_IDs",
                    "Date_Last_Modified", "Size_KB", "MD5", "Creating_Application", "Valid", "Well-Formed",
                    "Status_Message"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Reads the script output into a dataframe.
    # Provides a default MD5 value for data.xlsx and zipping.gz because fixity is different every time they are made.
    df_fits = pd.read_csv("accession_fits.csv")
    replace_md5 = (df_fits["File_Path"].str.endswith("data.xlsx")) | (df_fits["File_Path"].str.endswith("zipping.gz"))
    df_fits.loc[replace_md5, "MD5"] = "XXXXXXXXXX"

    # Compares the script output to the expected values.
    compare_dataframes("Make_FITS_CSV", df_fits, df_expected)

    # Deletes the test files.
    shutil.rmtree("accession")
    shutil.rmtree("accession_FITS")
    os.remove("accession_fits.csv")


def test_make_fits_csv_function_encoding_error():
    """Tests encoding error handling when saving FITS file data to the CSV."""

    # Makes an accession folder with plain text files.
    # Variations: one with no encoding error, two with encoding errors (from pi symbol and smiley face).
    accession_folder = fr"{output}\accession"
    os.makedirs(fr"{output}\accession\disk1")
    with open(r"accession\disk1\file.txt", "w") as file:
        file.write("Text" * 1000)
    with open(r"accession\disk1\pi_errorπ.txt", "w") as file:
        file.write("Text" * 2500)
    with open(r"accession\disk1\smiley_error.txt", "w") as file:
        file.write("Text" * 1500)

    # Makes FITS XML for the accession to use for testing.
    # In format_analysis.py, there is also error handling for if FITS has a load class error.
    fits_output = f"{output}/accession_FITS"
    os.mkdir(fits_output)
    subprocess.run(f'"{c.FITS}" -r -i "{accession_folder}" -o "{fits_output}"', shell=True)

    # RUNS THE FUNCTION BEING TESTED.
    make_fits_csv(fr"{output}\accession_FITS", accession_folder, output, "accession")

    # Makes a dataframe with the expected values for accession_encode_errors.txt.
    rows = [[fr"{output}\accession\disk1\pi_errorπ.txt"],
            [fr"{output}\accession\disk1\smiley_error.txt"]]
    df_encode_expected = pd.DataFrame(rows, columns=["Paths"])

    # Makes a dataframe with the expected values for accession_fits.csv.
    rows = [[fr"{output}\accession\disk1\file.txt", "Plain text", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/111",
             "Droid version 6.4; Jhove version 1.20.1; file utility version 5.03", False,
             datetime.date.today().strftime('%Y-%m-%d'), 4.0, "1a640a2c9c60ffea3174b2f73a536c48", np.NaN, True, True,
             np.NaN]]
    column_names = ["File_Path", "Format_Name", "Format_Version", "PUID", "Identifying_Tool(s)", "Multiple_IDs",
                    "Date_Last_Modified", "Size_KB", "MD5", "Creating_Application", "Valid", "Well-Formed",
                    "Status_Message"]
    df_fits_csv_expected = pd.DataFrame(rows, columns=column_names)

    # Reads the script outputs into dataframes.
    df_encode = pd.read_csv("accession_encode_errors.txt", header=None, names=["Paths"])
    df_fits_csv = pd.read_csv("accession_fits.csv")

    # Compares the script outputs to the expected values.
    compare_dataframes("Make_FITS_CSV_Error_Log", df_encode, df_encode_expected)
    compare_dataframes("Make_FITS_CSV_Error_CSV", df_fits_csv, df_fits_csv_expected)

    # Deletes the test files.
    shutil.rmtree("accession")
    shutil.rmtree("accession_FITS")
    os.remove("accession_encode_errors.txt")
    os.remove("accession_fits.csv")


def test_match_nara_risk_function():
    """Tests combining NARA risk information with FITS information to produce df_results."""

    # Makes a dataframe to use for FITS information.
    # PUID variations: match 1 PUID and multiple PUIDs
    # Name variations: match with version or name only, including case not matching
    # Extension variations: match single extension and pipe-separated extension, including case not matching
    # Also includes 2 that won't match
    rows = [[r"C:\PUID\file.zip", "ZIP archive", np.NaN, "https://www.nationalarchives.gov.uk/pronom/x-fmt/263"],
            [r"C:\PUID\3\movie.ifo", "DVD Data File", np.NaN, "https://www.nationalarchives.gov.uk/pronom/x-fmt/419"],
            [r"C:\Name\img.jp2", "JPEG 2000 File Format", np.NaN, np.NaN],
            [r"C:\Name\Case\file.gz", "gzip", np.NaN, np.NaN],
            [r"C:\Name\Version\database.nsf", "Lotus Notes Database", "2", np.NaN],
            [r"C:\Ext\Both\file.dat", "File Data", np.NaN, np.NaN],
            [r"C:\Ext\Case\file.BIN", "Unknown Binary", np.NaN, np.NaN],
            [r"C:\Ext\Multi\img.jpg", "JPEG", "1", np.NaN],
            [r"C:\Unmatched\file.new", "Brand New Format", np.NaN, np.NaN],
            [r"C:\Unmatched\file.none", "empty", np.NaN, np.NaN]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_PUID"]
    df_fits = pd.DataFrame(rows, columns=column_names)

    # Reads the NARA risk CSV into a dataframe.
    # In format_analysis.py, this is done in the main body of the script before the function is called.
    df_nara = csv_to_dataframe(c.NARA)

    # RUNS THE FUNCTION BEING TESTED.
    df_results = match_nara_risk(df_fits, df_nara)

    # Makes a dataframe with the expected values.
    rows = [[r"C:\PUID\file.zip", "ZIP archive", np.NaN, "https://www.nationalarchives.gov.uk/pronom/x-fmt/263",
             "ZIP archive", "zip", "https://www.nationalarchives.gov.uk/pronom/x-fmt/263", "Moderate Risk",
             "Retain but extract files from the container", "PRONOM"],
            [r"C:\PUID\3\movie.ifo", "DVD Data File", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/419", "DVD Data Backup File", "bup",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/419", "Moderate Risk", "Retain", "PRONOM"],
            [r"C:\PUID\3\movie.ifo", "DVD Data File", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/419", "DVD Data File", "dvd",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/419", "Moderate Risk", "Retain", "PRONOM"],
            [r"C:\PUID\3\movie.ifo", "DVD Data File", np.NaN,
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/419", "DVD Info File", "ifo",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/419", "Moderate Risk", "Retain", "PRONOM"],
            [r"C:\Name\img.jp2", "JPEG 2000 File Format", np.NaN, np.NaN, "JPEG 2000 File Format", "jp2",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/392", "Low Risk", "Retain", "Format Name"],
            [r"C:\Name\Case\file.gz", "gzip", np.NaN, np.NaN, "GZIP", "gz|tgz",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/266", "Low Risk",
             "Retain but extract files from the container", "Format Name"],
            [r"C:\Name\Version\database.nsf", "Lotus Notes Database", "2", np.NaN, "Lotus Notes Database 2",
             "nsf|ns2", "https://www.nationalarchives.gov.uk/pronom/x-fmt/336", "Moderate Risk", "Transform to CSV",
             "Format Name"],
            [r"C:\Ext\Both\file.dat", "File Data", np.NaN, np.NaN, "Data File", "dat", np.NaN, "Moderate Risk",
             "Retain", "File Extension"],
            [r"C:\Ext\Both\file.dat", "File Data", np.NaN, np.NaN, "Windows Registry Files", "reg|dat", np.NaN,
             "Moderate Risk", "Retain", "File Extension"],
            [r"C:\Ext\Case\file.BIN", "Unknown Binary", np.NaN, np.NaN, "Binary file", "bin",
             "https://www.nationalarchives.gov.uk/pronom/fmt/208", "High Risk", "Retain", "File Extension"],
            [r"C:\Ext\Multi\img.jpg", "JPEG", "1", np.NaN, "JPEG File Interchange Format 1.00", "jpg|jpeg",
             "https://www.nationalarchives.gov.uk/pronom/fmt/42", "Low Risk", "Retain", "File Extension"],
            [r"C:\Ext\Multi\img.jpg", "JPEG", "1", np.NaN, "JPEG File Interchange Format 1.01", "jpg|jpeg",
             "https://www.nationalarchives.gov.uk/pronom/fmt/43", "Low Risk", "Retain", "File Extension"],
            [r"C:\Ext\Multi\img.jpg", "JPEG", "1", np.NaN, "JPEG File Interchange Format 1.02", "jpg|jpeg",
             "https://www.nationalarchives.gov.uk/pronom/fmt/44", "Low Risk", "Retain", "File Extension"],
            [r"C:\Ext\Multi\img.jpg", "JPEG", "1", np.NaN, "JPEG Raw Stream", "jpg|jpeg",
             "https://www.nationalarchives.gov.uk/pronom/fmt/41", "Low Risk", "Retain", "File Extension"],
            [r"C:\Ext\Multi\img.jpg", "JPEG", "1", np.NaN, "JPEG unspecified version", "jpg|jpeg", np.NaN,
             "Low Risk", "Retain", "File Extension"],
            [r"C:\Unmatched\file.new", "Brand New Format", np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, "No Match",
             np.NaN, "No NARA Match"],
            [r"C:\Unmatched\file.none", "empty", np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, "No Match", np.NaN,
             "No NARA Match"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_PUID",
                    "NARA_Format Name", "NARA_File Extension(s)", "NARA_PRONOM URL", "NARA_Risk Level",
                    "NARA_Proposed Preservation Plan", "NARA_Match_Type"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Match_NARA_Risk", df_results, df_expected)


def test_match_technical_appraisal_function():
    """Tests adding technical appraisal categories to df_results, which already has information from FITS and NARA."""

    # Makes a dataframe to use as input.
    # Data variation: examples that match both, one, or neither of the technical appraisal categories,
    #                 with identical cases and different cases (match is case-insensitive),
    #                 and a folder that contains the word trash but shouldn't be identified for technical appraisal.
    rows = [[r"C:\CD1\Flower.JPG", "JPEG EXIF"],
            [r"C:\CD1\Trashes\Flower1.JPG", "JPEG EXIF"],
            [r"C:\CD2\Script\config.pyc", "unknown binary"],
            [r"C:\CD2\Trash Data\data.zip", "ZIP Format"],
            [r"C:\CD2\trash\New Document.txt", "Plain text"],
            [r"C:\CD2\Trash\New Text.txt", "Plain text"],
            [r"C:\FD1\empty.txt", "empty"],
            [r"C:\FD1\trashes\program.dll", "PE32 executable"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Reads the technical appraisal CSV into a dataframe.
    # In format_analysis.py, this is done in the main body of the script before the function is called.
    df_ita = csv_to_dataframe(c.ITA)

    # RUNS THE FUNCTION BEING TESTED.
    df_results = match_technical_appraisal(df_results, df_ita)

    # Makes a dataframe with the expected values.
    rows = [[r"C:\CD1\Flower.JPG", "JPEG EXIF", "Not for TA"],
            [r"C:\CD1\Trashes\Flower1.JPG", "JPEG EXIF", "Trash"],
            [r"C:\CD2\Script\config.pyc", "unknown binary", "Format"],
            [r"C:\CD2\Trash Data\data.zip", "ZIP Format", "Not for TA"],
            [r"C:\CD2\trash\New Document.txt", "Plain text", "Trash"],
            [r"C:\CD2\Trash\New Text.txt", "Plain text", "Trash"],
            [r"C:\FD1\empty.txt", "empty", "Format"],
            [r"C:\FD1\trashes\program.dll", "PE32 executable", "Trash"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "Technical Appraisal"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Match_Tech_Appraisal", df_results, df_expected)


def test_match_other_risk_function():
    """Tests adding other risk categories to df_results, which already has information from FITS, NARA,
    and technical appraisal."""

    # Makes a dataframe to use as input.
    # Data variation: examples that match both, one, or neither of the other risk categories,
    #                 with identical cases and different cases (match is case-insensitive),
    #                 and at least one each of the format risk criteria.
    rows = [["Adobe Photoshop file", "Moderate Risk", "Transform to TIFF or JPEG2000"],
            ["Cascading Style Sheet", "Low Risk", "Retain"],
            ["CorelDraw Drawing", "High Risk", "Transform to a TBD format, possibly PDF or TIFF"],
            ["empty", np.NaN, np.NaN],
            ["Encapsulated Postscript File", "Low Risk", "Transform to TIFF or JPEG2000"],
            ["iCalendar", "Low Risk", "Transform to CSV"],
            ["MBOX Email Format", "Low Risk", "Transform to EML but also retain MBOX"],
            ["Plain text", "Low Risk", "Retain"],
            ["zip format", "Low Risk", "Retain"]]
    column_names = ["FITS_Format_Name", "NARA_Risk Level", "NARA_Proposed Preservation Plan"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Reads the risk file formats CSV into a dataframe.
    # In format_analysis.py, this is done in the main body of the script before the function is called.
    df_other = csv_to_dataframe(c.RISK)

    # RUNS THE FUNCTION BEING TESTED.
    df_results = match_other_risk(df_results, df_other)

    # Makes a dataframe with the expected values.
    rows = [["Adobe Photoshop file", "Moderate Risk", "Transform to TIFF or JPEG2000", "Layered image file"],
            ["Cascading Style Sheet", "Low Risk", "Retain", "Possible saved web page"],
            ["CorelDraw Drawing", "High Risk", "Transform to a TBD format, possibly PDF or TIFF", "Layered image file"],
            ["empty", np.NaN, np.NaN, "Not for Other"],
            ["Encapsulated Postscript File", "Low Risk", "Transform to TIFF or JPEG2000", "Layered image file"],
            ["iCalendar", "Low Risk", "Transform to CSV", "NARA Low/Transform"],
            ["MBOX Email Format", "Low Risk", "Transform to EML but also retain MBOX", "NARA Low/Transform"],
            ["Plain text", "Low Risk", "Retain", "Not for Other"],
            ["zip format", "Low Risk", "Retain", "Archive format"]]
    column_names = ["FITS_Format_Name", "NARA_Risk Level", "NARA_Proposed Preservation Plan", "Other_Risk"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Match_Other_Risk", df_results, df_expected)


def test_deduplicating_results_df():
    """Tests that duplicates from multiple NARA matches with the same risk information are correctly removed.
    In format_analysis.py, this is done in the main body of the script."""

    # Makes a dataframe to use as input, with a subset of the columns usually in df_results.
    # Data variation: one FITS ID with one NARA match, multiple FITS IDs with one NARA match each,
    #                 multiple NARA matches with the same risk, multiple NARA matches with different risks.
    rows = [[r"C:\acc\disk1\data.csv", "Comma-Separated Values (CSV)", "Comma Separated Values", "csv",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/18", "Low Risk", "Retain"],
            [r"C:\acc\disk1\data.xlsx", "Open Office XML Workbook", "Microsoft Excel Office Open XML", "xlsx",
             "https://www.nationalarchives.gov.uk/pronom/fmt/214", "Low Risk", "Retain"],
            [r"C:\acc\disk1\data.xlsx", "XLSX", "Microsoft Excel Office Open XML", "xlsx",
             "https://www.nationalarchives.gov.uk/pronom/fmt/214", "Low Risk", "Retain"],
            [r"C:\acc\disk1\empty.txt", "empty", "ASCII 7-bit Text", "txt|asc|csv|tab",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/22", "Low Risk", "Retain"],
            [r"C:\acc\disk1\empty.txt", "empty", "ASCII 8-bit Text", "txt|asc|csv|tab",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/283", "Low Risk", "Retain"],
            [r"C:\acc\disk1\empty.txt", "empty", "JSON", "json|txt",
             "https://www.nationalarchives.gov.uk/pronom/fmt/817", "Low Risk", "Retain"],
            [r"C:\acc\disk1\empty.txt", "empty", "Plain Text", "Plain_Text|txt|text|asc|rte",
             "https://www.nationalarchives.gov.uk/pronom/x-fmt/111", "Low Risk", "Retain"],
            [r"C:\acc\disk1\file.pdf", "PDF", "Portable Document Format (PDF) version 1.7", "pdf",
             "https://www.nationalarchives.gov.uk/pronom/fmt/276", "Moderate Risk", "Retain"],
            [r"C:\acc\disk1\file.pdf", "PDF", "Portable Document Format (PDF) version 2.0", "pdf",
             "https://www.nationalarchives.gov.uk/pronom/fmt/1129", "Moderate Risk", "Retain"],
            [r"C:\acc\disk1\file.pdf", "PDF", "Portable Document Format/Archiving (PDF/A-1a) accessible", "pdf",
             "https://www.nationalarchives.gov.uk/pronom/fmt/95", "Low Risk", "Retain"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "NARA_Format Name", "NARA_File Extension(s)",
                    "NARA_PRONOM URL", "NARA_Risk Level", "NARA_Proposed Preservation Plan"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE BEING TESTED: Removes columns with NARA identification info and then removes duplicate rows.
    df_results.drop(["NARA_Format Name", "NARA_File Extension(s)", "NARA_PRONOM URL"], inplace=True, axis=1)
    df_results.drop_duplicates(inplace=True)

    # Makes a dataframe with the expected values.
    rows = [[r"C:\acc\disk1\data.csv", "Comma-Separated Values (CSV)", "Low Risk", "Retain"],
            [r"C:\acc\disk1\data.xlsx", "Open Office XML Workbook", "Low Risk", "Retain"],
            [r"C:\acc\disk1\data.xlsx", "XLSX", "Low Risk", "Retain"],
            [r"C:\acc\disk1\empty.txt", "empty", "Low Risk", "Retain"],
            [r"C:\acc\disk1\file.pdf", "PDF", "Moderate Risk", "Retain"],
            [r"C:\acc\disk1\file.pdf", "PDF", "Low Risk", "Retain"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "NARA_Risk Level", "NARA_Proposed Preservation Plan"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Deduplicate_Results_DF", df_results, df_expected)


def test_nara_risk_subset():
    """Tests the NARA risk subset, which is based on the NARA_Risk Level column."""

    # Makes a dataframe to use as input.
    # Data variation: all 4 risk levels and all columns to be dropped.
    rows = [[r"C:\Disk1\file.txt", "Plain text", "Low Risk", "drop", "drop", "drop", "drop", "drop", "drop"],
            [r"C:\Disk1\photo.jpg", "JPEG EXIF", "Low Risk", "drop", "drop", "drop", "drop", "drop", "drop"],
            [r"C:\Disk1\file.psd", "Adobe Photoshop file", "Moderate Risk", "drop", "drop", "drop", "drop", "drop", "drop"],
            [r"C:\Disk1\file.bak", "Backup File", "High Risk", "drop", "drop", "drop", "drop", "drop", "drop"],
            [r"C:\Disk1\new.txt", "empty", "No Match", "drop", "drop", "drop", "drop", "drop", "drop"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "NARA_Risk Level", "FITS_PUID", "FITS_Identifying_Tool(s)",
                    "FITS_Creating_Application", "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE TO BE TESTED: filters the dataframe to the correct subset and removes unwanted columns.
    # In format_analysis.py, this is done in the main body of the script.
    df_nara_risk = df_results[df_results["NARA_Risk Level"] != "Low Risk"].copy()
    df_nara_risk.drop(["FITS_PUID", "FITS_Identifying_Tool(s)", "FITS_Creating_Application",
                       "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"], inplace=True, axis=1)

    # Makes a dataframe with the expected values.
    rows = [[r"C:\Disk1\file.psd", "Adobe Photoshop file", "Moderate Risk"],
            [r"C:\Disk1\file.bak", "Backup File", "High Risk"],
            [r"C:\Disk1\new.txt", "empty", "No Match"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "NARA_Risk Level"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("NARA_Risk_Subset", df_nara_risk, df_expected)


def test_multiple_ids_subset():
    """Tests the files with multiple FITs format ids subset, which is based on the FITS_File_Path column."""

    # Makes a dataframe to use as input.
    # Data variation: files with multiple ids and files without; all columns to be dropped.
    rows = [[r"C:\Disk1\file1.txt", "Plain text", False, "drop", "drop", "drop"],
            [r"C:\Disk1\file2.html", "Hypertext Markup Language", True, "drop", "drop", "drop"],
            [r"C:\Disk1\file2.html", "HTML Transitional", True, "drop", "drop", "drop"],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Document", True, "drop", "drop", "drop"],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Workbook", True, "drop", "drop", "drop"],
            [r"C:\Disk1\file3.xlsx", "XLSX", True, "drop", "drop", "drop"],
            [r"C:\Disk1\photo.jpg", "JPEG EXIF", False, "drop", "drop", "drop"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Multiple_IDs",
                    "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE TO BE TESTED: filters the dataframe to the correct subset and removes unwanted columns.
    # In format_analysis.py, this is done in the main body of the script.
    df_multiple = df_results[df_results.duplicated("FITS_File_Path", keep=False) == True].copy()
    df_multiple.drop(["FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"], inplace=True, axis=1)

    # Makes a dataframe with the expected values.
    rows = [[r"C:\Disk1\file2.html", "Hypertext Markup Language", True],
            [r"C:\Disk1\file2.html", "HTML Transitional", True],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Document", True],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Workbook", True],
            [r"C:\Disk1\file3.xlsx", "XLSX", True]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Multiple_IDs"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Multiple_IDs_Subset", df_multiple, df_expected)


def test_validation_subset():
    """Tests the FITS validation subset, which is based on the FITS_Valid, FITS_Well-Formed,
    and FITS_Status_Message columns."""

    # Makes a dataframe to use as input.
    # Data variation: values in 0, 1, 2, or 3 columns will include the file in the validation subset.
    # Some of these combinations probably wouldn't happen in real data, but want to be thorough.
    rows = [[r"C:\Disk1\file1.txt", "Plain text", True, True, np.NaN],
            [r"C:\Disk1\file2.html", "Hypertext Markup Language", np.NaN, np.NaN, np.NaN],
            [r"C:\Disk1\file2.html", "HTML Transitional", False, True, np.NaN],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Document", True, False, np.NaN],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Workbook", True, True, "Validation Error"],
            [r"C:\Disk1\file3.xlsx", "XLSX", False, False, np.NaN],
            [r"C:\Disk1\photo.jpg", "JPEG EXIF", True, False, "Validation Error"],
            [r"C:\Disk1\photo1.jpg", "JPEG EXIF", False, True, "Validation Error"],
            [r"C:\Disk1\photo2.jpg", "JPEG EXIF", False, False, "Validation Error"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE TO BE TESTED: filters the dataframe to the correct subset.
    # In format_analysis.py, this is done in the main body of the script.
    df_validation = df_results[(df_results["FITS_Valid"] == False) | (df_results["FITS_Well-Formed"] == False) |
                               (df_results["FITS_Status_Message"].notnull())].copy()

    # Makes a dataframe with the expected values.
    rows = [[r"C:\Disk1\file2.html", "HTML Transitional", False, True, np.NaN],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Document", True, False, np.NaN],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Workbook", True, True, "Validation Error"],
            [r"C:\Disk1\file3.xlsx", "XLSX", False, False, np.NaN],
            [r"C:\Disk1\photo.jpg", "JPEG EXIF", True, False, "Validation Error"],
            [r"C:\Disk1\photo1.jpg", "JPEG EXIF", False, True, "Validation Error"],
            [r"C:\Disk1\photo2.jpg", "JPEG EXIF", False, False, "Validation Error"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Validation_Subset", df_validation, df_expected)


def test_tech_appraisal_subset():
    """Tests the technical appraisal subset, which is based on the Technical_Appraisal column."""

    # Makes a dataframe to use as input.
    # Data variation: all 3 technical appraisal categories and all columns to drop.
    rows = [["DOS/Windows Executable", "Format", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["JPEG EXIF", "Not for TA", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["Unknown Binary", "Format", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["Plain text", "Not for TA", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["JPEG EXIF", "Trash", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["Open Office XML Workbook", "Trash", "drop", "drop", "drop", "drop", "drop", "drop"]]
    column_names = ["FITS_Format_Name", "Technical_Appraisal", "FITS_PUID", "FITS_Date_Last_Modified",
                    "FITS_MD5", "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE TO BE TESTED: filters the dataframe to the correct subset and removes unwanted columns.
    # In format_analysis.py, this is done in the main body of the script.
    df_tech_appraisal = df_results[df_results["Technical_Appraisal"] != "Not for TA"].copy()
    df_tech_appraisal.drop(["FITS_PUID", "FITS_Date_Last_Modified", "FITS_MD5", "FITS_Valid", "FITS_Well-Formed",
                            "FITS_Status_Message"], inplace=True, axis=1)

    # Makes a dataframe with the expected values.
    rows = [["DOS/Windows Executable", "Format"],
            ["Unknown Binary", "Format"],
            ["JPEG EXIF", "Trash"],
            ["Open Office XML Workbook", "Trash"]]
    column_names = ["FITS_Format_Name", "Technical_Appraisal"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Tech_Appraisal_Subset", df_tech_appraisal, df_expected)


def test_other_risk_subset():
    """Tests the other risk subset, which is based on the Other_Risk column."""

    # Makes a dataframe to use as input.
    # Data variation: all other risk categories and all columns to drop.
    rows = [["DOS/Windows Executable", "Not for Other", "drop", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["Adobe Photoshop file", "Layered image file", "drop", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["JPEG EXIF", "Not for Other", "drop", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["Cascading Style Sheet", "Possible saved web page", "drop", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["iCalendar", "NARA Low/Transform", "drop", "drop", "drop", "drop", "drop", "drop", "drop"],
            ["Zip Format", "Archive format", "drop", "drop", "drop", "drop", "drop", "drop", "drop"]]
    column_names = ["FITS_Format_Name", "Other_Risk", "FITS_PUID", "FITS_Date_Last_Modified", "FITS_MD5",
                    "FITS_Creating_Application", "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE TO BE TESTED: filters the dataframe to the correct subset and removes unwanted columns.
    # In format_analysis.py, this is done in the main body of the script.
    df_other_risk = df_results[df_results["Other_Risk"] != "Not for Other"].copy()
    df_other_risk.drop(["FITS_PUID", "FITS_Date_Last_Modified", "FITS_MD5", "FITS_Creating_Application", "FITS_Valid",
                        "FITS_Well-Formed", "FITS_Status_Message"], inplace=True, axis=1)

    # Makes a dataframe with the expected values.
    rows = [["Adobe Photoshop file", "Layered image file"],
            ["Cascading Style Sheet", "Possible saved web page"],
            ["iCalendar", "NARA Low/Transform"],
            ["Zip Format", "Archive format"]]
    column_names = ["FITS_Format_Name", "Other_Risk"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Other_Risk_Subset", df_other_risk, df_expected)


def test_duplicates_subset():
    """Tests the duplicates subset, which is based on the FITS_File_Path and FITS_MD5 columns."""

    # Makes a dataframe to use as input.
    # Data variation: unique files, files duplicate because of multiple FITs file ids, and real duplicate files.
    rows = [[r"C:\Disk1\file1.txt", "Plain text", 0.004, "098f6bcd4621d373cade4e832627b4f6"],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Document", 19.316, "b66e2fa385872d1a16d31b00f4b5f035"],
            [r"C:\Disk1\file3.xlsx", "Open Office XML Workbook", 19.316, "b66e2fa385872d1a16d31b00f4b5f035"],
            [r"C:\Disk1\file3.xlsx", "XLSX", 19.316, "b66e2fa385872d1a16d31b00f4b5f035"],
            [r"C:\Disk1\photo.jpg", "JPEG EXIF", 13.563, "686779fae835aadff6474898f5781e99"],
            [r"C:\Disk2\file1.txt", "Plain text", 0.004, "098f6bcd4621d373cade4e832627b4f6"],
            [r"C:\Disk3\file1.txt", "Plain text", 0.004, "098f6bcd4621d373cade4e832627b4f6"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Size_KB", "FITS_MD5"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE CODE TO BE TESTED: filters the dataframe to the correct subset and removes unwanted columns.
    # In format_analysis.py, this is done in the main body of the script.
    df_duplicates = df_results[["FITS_File_Path", "FITS_Size_KB", "FITS_MD5"]].copy()
    df_duplicates = df_duplicates.drop_duplicates(subset=["FITS_File_Path"], keep=False)
    df_duplicates = df_duplicates.loc[df_duplicates.duplicated(subset="FITS_MD5", keep=False)]

    # Makes a dataframe with the expected values.
    rows = [[r"C:\Disk1\file1.txt", 0.004, "098f6bcd4621d373cade4e832627b4f6"],
            [r"C:\Disk2\file1.txt", 0.004, "098f6bcd4621d373cade4e832627b4f6"],
            [r"C:\Disk3\file1.txt", 0.004, "098f6bcd4621d373cade4e832627b4f6"]]
    column_names = ["FITS_File_Path", "FITS_Size_KB", "FITS_MD5"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Duplicates_Subset", df_duplicates, df_expected)


def test_empty_subset():
    """Tests handling of an empty subset, which can happen with any subset.
    Using the file with multiple format ids and duplicate MD5s subsets for testing."""

    # Makes a dataframe to use as input where all files have a unique identification and unique MD5.
    rows = [[r"C:\Disk1\file1.txt", "Plain text", 0.004, "098f6bcd4621d373cade4e832627b4f6"],
            [r"C:\Disk1\file2.txt", "Plain text", 5.347, "c9f6d785a33cfac2cc1f51ab4704b8a1"],
            [r"C:\Disk2\file3.pdf", "Portable Document Format", 187.972, "6dfeecf4e4200a0ad147a7271a094e68"],
            [r"c:\Disk2\file4.txt", "Plain text", 0.178, "97e4f6e6f35e5606855d0917e22740b9"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Size_KB", "FITS_MD5"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Calculates both subsets.
    # In format_analysis.py, this is done in the main body of the script.

    df_multiple_ids = df_results[df_results.duplicated("FITS_File_Path", keep=False) == True].copy()

    df_duplicates = df_results[["FITS_File_Path", "FITS_Size_KB", "FITS_MD5"]].copy()
    df_duplicates = df_duplicates.drop_duplicates(subset=["FITS_File_Path"], keep=False)
    df_duplicates = df_duplicates.loc[df_duplicates.duplicated(subset="FITS_MD5", keep=False)]

    # RUNS THE CODE BEING TESTED: Tests each subset for if they are empty and supplies default text.
    # In format_analysis.py, this is done in the main body of the script
    # and includes all 6 subset dataframes in the tuple.
    for df in (df_multiple_ids, df_duplicates):
        if len(df) == 0:
            df.loc[len(df)] = ["No data of this type"] + [np.NaN] * (len(df.columns) - 1)

    # Makes dataframes with the expected values for each subset.

    rows = [["No data of this type", np.NaN, np.NaN, np.NaN]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Size_KB", "FITS_MD5"]
    df_multiple_ids_expected = pd.DataFrame(rows, columns=column_names)

    rows = [["No data of this type", np.NaN, np.NaN]]
    column_names = ["FITS_File_Path", "FITS_Size_KB", "FITS_MD5"]
    df_duplicates_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values for each subset.
    compare_dataframes("Empty_Multiple_IDs_Subset", df_multiple_ids, df_multiple_ids_expected)
    compare_dataframes("Empty_Duplicate_Subset", df_duplicates, df_duplicates_expected)


def test_format_subtotal():
    """Tests the format subtotal, which is based on FITS_Format_Name and NARA_Risk Level."""

    # Makes a dataframe to use as input for the subtotal() function.
    # Data variation: formats with one row, formats with multiple rows, one format with a NARA risk level,
    #                 multiple formats with a NARA risk level, blank in NARA risk level.
    rows = [["JPEG EXIF", 13.563, "Low Risk"],
            ["JPEG EXIF", 14.1, "Low Risk"],
            ["Open Office XML Workbook", 19.316, "Low Risk"],
            ["Unknown Binary", 0, np.NaN],
            ["Unknown Binary", 1, np.NaN],
            ["Unknown Binary", 5, np.NaN],
            ["XLSX", 19.316, "Low Risk"],
            ["Zip Format", 2.792, "Moderate Risk"]]
    column_names = ["FITS_Format_Name", "FITS_Size_KB", "NARA_Risk Level"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Calculates the total files and total size in the dataframe to use for percentages with the subtotal.
    # In format_analysis.py, this is done in the main body of the script before subtotal() is called.
    totals_dict = {"Files": len(df_results.index), "MB": df_results["FITS_Size_KB"].sum() / 1000}

    # RUNS THE FUNCTION BEING TESTED.
    df_format_subtotal = subtotal(df_results, ["FITS_Format_Name", "NARA_Risk Level"], totals_dict)

    # Makes a dataframe with the expected values.
    # The index values for the dataframe made by subtotal() are column values here
    # so that they are visible in the comparison dataframe to label errors.
    rows = [["JPEG EXIF", "Low Risk", 2, 25, 0.028, 37.29],
            ["Unknown Binary", np.NaN, 3, 37.5, 0.006, 7.991],
            ["Zip Format", "Moderate Risk", 1, 12.5, 0.003, 3.995],
            ["Open Office XML Workbook", "Low Risk", 1, 12.5, 0.019, 25.304],
            ["XLSX", "Low Risk", 1, 12.5, 0.019, 25.304]]
    column_names = ["FITS_Format_Name", "NARA_Risk Level", "File Count", "File %", "Size (MB)", "Size %"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Format_Subtotal", df_format_subtotal, df_expected)


def test_nara_risk_subtotal():
    """Tests the NARA risk subtotal, which is based on NARA_Risk Level."""

    # Makes a dataframe to use as input for the subtotal() function.
    # Data variation: one format with a NARA risk level, multiple formats with a NARA risk level, all 4 risk levels.
    rows = [["DOS/Windows Executable", 1.23, "High Risk"],
            ["DOS/Windows Executable", 2.34, "High Risk"],
            ["DOS/Windows Executable", 3.45, "High Risk"],
            ["JPEG EXIF", 13.563, "Low Risk"],
            ["JPEG EXIF", 14.1, "Low Risk"],
            ["Open Office XML Workbook", 19.316, "Low Risk"],
            ["Unknown Binary", 0, "No Match"],
            ["Unknown Binary", 5, "No Match"],
            ["XLSX", 19.316, "Low Risk"],
            ["Zip Format", 2.792, "Moderate Risk"]]
    column_names = ["FITS_Format_Name", "FITS_Size_KB", "NARA_Risk Level"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Calculates the total files and total size in the dataframe to use for percentages with the subtotal.
    # In format_analysis.py, this is done in the main body of the script before subtotal() is called.
    totals_dict = {"Files": len(df_results.index), "MB": df_results["FITS_Size_KB"].sum() / 1000}

    # RUNS THE FUNCTION BEING TESTED.
    df_nara_risk_subtotal = subtotal(df_results, ["NARA_Risk Level"], totals_dict)

    # Makes a dataframe with the expected values.
    # The index value for the dataframe made by subtotal() is a column value here
    # so that it is visible in the comparison dataframe to label errors.
    rows = [["Low Risk", 4, 40, 0.066, 81.374],
            ["Moderate Risk", 1, 10, 0.003, 3.699],
            ["High Risk", 3, 30, 0.007, 8.631],
            ["No Match", 2, 20, 0.005, 6.165]]
    column_names = ["NARA_Risk Level", "File Count", "File %", "Size (MB)", "Size %"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("NARA_Risk_Subtotal", df_nara_risk_subtotal, df_expected)


def test_tech_appraisal_subtotal():
    """Tests the technical appraisal subtotal, which is based on technical appraisal criteria and FITS_Format_Name."""

    # Makes a dataframe to use as input for the subtotal() function.
    # Data variation: for both criteria, has a unique format and duplicated formats.
    rows = [["Format", "DOS/Windows Executable", 100.23],
            ["Format", "DOS/Windows Executable", 200.34],
            ["Format", "PE32 executable", 300.45],
            ["Format", "Unknown Binary", 0],
            ["Format", "Unknown Binary", 50],
            ["Trash", "JPEG EXIF", 130.563],
            ["Trash", "JPEG EXIF", 140.1],
            ["Trash", "Open Office XML Workbook", 190.316]]
    column_names = ["Technical_Appraisal", "FITS_Format_Name", "FITS_Size_KB"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Calculates the total files and total size in the dataframe to use for percentages with the subtotal.
    # In format_analysis.py, this is done in the main body of the script before subtotal() is called.
    totals_dict = {"Files": len(df_results.index), "MB": df_results["FITS_Size_KB"].sum() / 1000}

    # RUNS THE FUNCTION BEING TESTED.
    df_tech_appraisal_subtotal = subtotal(df_results, ["Technical_Appraisal", "FITS_Format_Name"], totals_dict)

    # Makes a dataframe with the expected values.
    # The index values for the dataframes made by subtotal() are column values here
    # so that they are visible in the comparison dataframe to label errors.
    rows = [["Format", "DOS/Windows Executable", 2, 25, 0.301, 27.068],
            ["Format", "PE32 executable", 1, 12.5, 0.300, 26.978],
            ["Format", "Unknown Binary", 2, 25, 0.05, 4.496],
            ["Trash", "JPEG EXIF", 2, 25, 0.271, 24.371],
            ["Trash", "Open Office XML Workbook", 1, 12.5, 0.19, 17.086]]
    column_names = ["Technical_Appraisal", "FITS_Format_Name", "File Count", "File %", "Size (MB)", "Size %"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Tech_Appraisal_Subtotal", df_tech_appraisal_subtotal, df_expected)


def test_tech_appraisal_subtotal_none():
    """Tests the technical appraisal subtotal when there are no files in the input
    which meet any technical appraisal criteria."""

    # Makes an empty dataframe to use as input for the subtotal() function.
    df_results = pd.DataFrame(columns=["Technical_Appraisal", "FITS_Format_Name", "FITS_Size_KB"])

    # Calculates the total files and total size in the dataframe to use for percentages with the subtotal.
    # In format_analysis.py, this is done in the main body of the script before subtotal() is called.
    totals_dict = {"Files": len(df_results.index), "MB": df_results["FITS_Size_KB"].sum() / 1000}

    # RUNS THE FUNCTION BEING TESTED.
    df_tech_appraisal_subtotal = subtotal(df_results, ["Technical_Appraisal", "FITS_Format_Name"], totals_dict)

    # Makes a dataframe with the expected values.
    rows = [["No data of this type", np.NaN, np.NaN, np.NaN]]
    column_names = ["File Count", "File %", "Size (MB)", "Size %"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Tech_Appraisal_Subtotal_None", df_tech_appraisal_subtotal, df_expected)


def test_other_risk_subtotal():
    """Tests the other risk subtotal, which is based on other risk criteria and FITS_Format_Name."""

    # Makes a dataframe to use as input for the subtotal() function.
    # Data variation: for each of the values for other risk, has unique formats and duplicated formats.
    rows = [["Not for Other", "DOS/Windows Executable", 100.23],
            ["Not for Other", "JPEG EXIF", 1300.563],
            ["Not for Other", "JPEG EXIF", 1400.1],
            ["Not for Other", "JPEG EXIF", 1900.316],
            ["Not for Other", "PE32 Executable", 200.34],
            ["Possible saved web page", "Cascading Style Sheet", 10000],
            ["Archive format", "Zip Format", 20000],
            ["Archive format", "Zip Format", 20000],
            ["Archive format", "Zip Format", 30000],
            ["Archive format", "Zip Format", 30000]]
    column_names = ["Other_Risk", "FITS_Format_Name", "FITS_Size_KB"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # Calculates the total files and total size in the dataframe to use for percentages with the subtotal.
    # In format_analysis.py, this is done in the main body of the script before subtotal() is called.
    totals_dict = {"Files": len(df_results.index), "MB": df_results["FITS_Size_KB"].sum() / 1000}

    # RUNS THE FUNCTION BEING TESTED.
    df_other_risk_subtotal = subtotal(df_results, ["Other_Risk", "FITS_Format_Name"], totals_dict)

    # Makes a dataframe with the expected values.
    # The index values for the dataframes made by subtotal() are column values here
    # so that they are visible in the comparison dataframe to label errors.
    rows = [["Not for Other", "DOS/Windows Executable", 1, 10, 0.1, 0.087],
            ["Not for Other", "JPEG EXIF", 3, 30, 4.601, 4.004],
            ["Not for Other", "PE32 Executable", 1, 10, 0.2, 0.174],
            ["Possible saved web page", "Cascading Style Sheet", 1, 10, 10, 8.703],
            ["Archive format", "ZIP Format", 4, 40, 100, 87.031]]
    column_names = ["Other_Risk", "FITS_Format_Name", "File Count", "File %", "Size (MB)", "Size %"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Other_Risk_Subtotal", df_other_risk_subtotal, df_expected)


def test_other_risk_subtotal_none():
    """Tests the other risk subtotal when there are no files in the input which meet any other risk criteria."""

    # Makes an empty dataframe to use as input for the subtotal() function.
    df_results = pd.DataFrame(columns=["Other_Risk", "FITS_Format_Name", "FITS_Size_KB"])

    # Calculates the total files and total size in the dataframe to use for percentages with the subtotal.
    # In format_analysis.py, this is done in the main body of the script before subtotal() is called.
    totals_dict = {"Files": len(df_results.index), "MB": df_results["FITS_Size_KB"].sum() / 1000}

    # RUNS THE FUNCTION BEING TESTED.
    df_other_risk_subtotal = subtotal(df_results, ["Other_Risk", "FITS_Format_Name"], totals_dict)

    # Makes a dataframe with the expected values.
    rows = [["No data of this type", np.NaN, np.NaN, np.NaN]]
    column_names = ["File Count", "File %", "Size (MB)", "Size %"]
    df_expected = pd.DataFrame(rows, columns=column_names)

    # Compares the script output to the expected values.
    compare_dataframes("Other_Risk_Subtotal_None", df_other_risk_subtotal, df_expected)


def test_media_subtotal_function():
    """Tests variations in subtotal."""

    # Makes a dataframe and accession_folder variable to use as input.
    # Data variations: Disks with and without each risk type, unique values and values to add for subtotal.
    accession_folder = r"C:\ACC"
    rows = [[r"C:\ACC\Disk1\file.txt", 120, "Low Risk", "Not for TA", "Not for Other"],
            [r"C:\ACC\Disk1\file2.txt", 130, "Low Risk", "Not for TA", "Not for Other"],
            [r"C:\ACC\Disk1\file3.txt", 140, "Low Risk", "Not for TA", "Not for Other"],
            [r"C:\ACC\Disk2\photo.jpg", 12345, "Low Risk", "Not for TA", "Not for Other"],
            [r"C:\ACC\Disk2\file.psd", 15671, "Moderate Risk", "Not for TA", "Layered image file"],
            [r"C:\ACC\Disk2\file1.psd", 15672, "Moderate Risk", "Not for TA", "Layered image file"],
            [r"C:\ACC\Disk2\file2.psd", 15673, "Moderate Risk", "Not for TA", "Layered image file"],
            [r"C:\ACC\Disk2\file.bak", 700, "High Risk", "Not for TA", "Not for Other"],
            [r"C:\ACC\Disk2\empty.ext", 0, "No Match", "Format", "Not for Other"],
            [r"C:\ACC\Disk2\empty1.ext", 0, "No Match", "Format", "Not for Other"],
            [r"C:\ACC\Disk3\trash\file.bak", 700, "High Risk", "Trash", "Not for Other"],
            [r"C:\ACC\Disk3\trash\empty.ext", 0, "No Match", "Trash", "Not for Other"],
            [r"C:\ACC\Disk3\file.exe", 50, "High Risk", "Format", "Not for Other"],
            [r"C:\ACC\Disk3\file.psd", 1567, "Moderate Risk", "Trash", "Layered image file"],
            [r"C:\ACC\Disk4\file.css", 123, "Low Risk", "Not for TA", "Possible saved web page"],
            [r"C:\ACC\Disk4\file.ics", 14455, "Low Risk", "Not for TA", "NARA Low/Transform"],
            [r"C:\ACC\Disk4\draft\file.css", 125, "Low Risk", "Not for TA", "Possible saved web page"],
            [r"C:\ACC\Disk4\draft\file.ics", 14457, "Low Risk", "Not for TA", "NARA Low/Transform"],
            [r"C:\ACC\Disk4\draft\file.zip", 3399, "Moderate Risk", "Not for TA", "Archive format"],
            [r"C:\ACC\Disk4\draft2\file.css", 145, "Low Risk", "Not for TA", "Possible saved web page"],
            [r"C:\ACC\Disk4\draft2\file.ics", 116000, "Low Risk", "Not for TA", "NARA Low/Transform"],
            [r"C:\ACC\log.txt", 12, "Low Risk", "Not for TA", "Not for Other"]]
    column_names = ["FITS_File_Path", "FITS_Size_KB", "NARA_Risk Level", "Technical_Appraisal", "Other_Risk"]
    df_results = pd.DataFrame(rows, columns=column_names)

    # RUNS THE FUNCTION BEING TESTED.
    df_media_subtotal = media_subtotal(df_results, accession_folder)

    # Makes a dataframe with the expected values.
    rows = [["Disk1", 3, 0.39, 0, 0, 3, 0, 0, 0],
            ["Disk2", 7, 60.061, 1, 3, 1, 2, 2, 3],
            ["Disk3", 4, 2.317, 2, 1, 0, 1, 1, 1],
            ["Disk4", 7, 148.704, 0, 1, 6, 0, 0, 7]]
    column_names = ["Media", "File Count", "Size (MB)", "NARA High Risk (File Count)",
                    "NARA Moderate Risk (File Count)", "NARA Low Risk (File Count)", "No NARA Match (File Count)",
                    "Technical Appraisal_Format (File Count)", "Other Risk Indicator (File Count)"]
    df_expected = pd.DataFrame(rows, columns=column_names)
    df_expected.set_index("Media")

    # Compares the script output to the expected values.
    compare_dataframes("Media_Subtotal", df_media_subtotal, df_expected)


def test_iteration(repo_path):
    """Tests that the script follows the correct logic based on the contents of the accession folder and
    that the contents are updated correctly. Runs the script 3 times to check all iterations: start from scratch,
    use existing FITS files (updating to match the accession folder), and use existing full risk data csv."""

    # Makes an accession folder with test files organized into 2 disks to use for testing.
    # All subtotals and subsets in the final report will have some information.
    # Formats included: csv, html, plain text, xlsx, zip
    # Variations: duplicate files, empty file, file with multiple identifications (xlsx),
    #             file with validation error (html), technical appraisal (empty, trash), other risk (zip)
    accession_folder = fr"{output}\accession"
    os.makedirs(fr"{accession_folder}\disk1\trash")
    with open(r"accession\disk1\trash\trash.txt", "w") as file:
        file.write("Trash Text " * 20)
    with open(r"accession\disk1\trash\trash1.txt", "w") as file:
        file.write("Trash Text " * 21)
    with open(r"accession\disk1\trash\trash2.txt", "w") as file:
        file.write("Trash Text " * 22)
    df_spreadsheet = pd.DataFrame()
    df_spreadsheet[["C1", "C2", "C2", "C3", "C4", "C5"]] = "Text" * 5000
    df_spreadsheet = pd.concat([df_spreadsheet]*3000, ignore_index=True)
    df_spreadsheet.to_excel(r"accession\disk1\data.xlsx", index=False)
    with open(r"accession\disk1\duplicate_file.txt", "w") as file:
        file.write("Text" * 900)
    os.makedirs(fr"{accession_folder}\disk2")
    shutil.make_archive(r"accession\disk2\disk1backup", 'zip', r"accession\disk1")
    shutil.copyfile(r"accession\disk2\disk1backup.zip", r"accession\disk2\disk1backup2.zip")
    shutil.copyfile(r"accession\disk2\disk1backup.zip", r"accession\disk2\disk1backup3.zip")
    shutil.copyfile(r"accession\disk1\duplicate_file.txt", r"accession\disk2\duplicate_file.txt")
    open(r"accession\disk2\empty.txt", "w").close()
    with open(r"accession\disk2\error.html", "w") as file:
        file.write("<body>This isn't really html</body>")

    # Calculates the path for running the format_analysis.py script.
    script_path = os.path.join(repo_path, "format_analysis.py")

    # ROUND ONE: Runs the script on the test accession folder and tests if the expected messages were produced.
    # In format_analysis.py, these messages are printed to the terminal for archivist review.
    iteration_one = subprocess.run(f"python {script_path} {accession_folder}", shell=True, stdout=subprocess.PIPE)
    msg = "\r\nGenerating new FITS format identification information.\r\n\r\n" \
          "Generating new risk data for the analysis report.\r\n"
    compare_strings("Iteration_Message_1", iteration_one.stdout.decode("utf-8"), msg)

    # ROUND TWO: Deletes the trash folder and adds a file to the accession folder to simulate archivist appraisal.
    # Also deletes the full_risk_data.csv so an updated one will be made with the changes.
    shutil.rmtree(r"accession\disk1\trash")
    with open(r"accession\disk2\new.txt", "w") as file:
        file.write("Text"*300)
    os.remove("accession_full_risk_data.csv")

    # Runs the script again on the test accession folder.
    # It will update the FITS files to match the accession folder and update the three spreadsheet.
    iteration_two = subprocess.run(f"python {script_path} {accession_folder}", shell=True, stdout=subprocess.PIPE)
    msg = "\r\nUpdating the XML files in the FITS folder to match the files in the accession folder.\r\n" \
          "This will update fits.csv but will NOT update full_risk_data.csv from a previous script iteration.\r\n" \
          "Delete full_risk_data.csv before the script gets to that step for it to be remade with the new information.\r\n\r\n" \
          "Generating new risk data for the analysis report.\r\n"
    compare_strings("Iteration_Message_2", iteration_two.stdout.decode("utf-8"), msg)

    # ROUND THREE: Edits the full_risk_data.csv to simulate archivist cleaning up risk matches.
    # Removes the data_update.final.xlsx FITS id of Zip Format and NARA matches to empty.txt except for Plain Text.
    df_risk = pd.read_csv("accession_full_risk_data.csv")
    xlsx_to_drop = df_risk[(df_risk["FITS_File_Path"] == fr"{accession_folder}\disk1\data.xlsx") &
                           (df_risk["FITS_Format_Name"] == "ZIP Format")]
    empty_to_drop = df_risk[(df_risk["FITS_File_Path"] == fr"{accession_folder}\disk2\empty.txt") & 
                            (df_risk["NARA_Format Name"] != "Plain Text")]
    df_risk.drop(xlsx_to_drop.index, inplace=True)
    df_risk.drop(empty_to_drop.index, inplace=True)
    df_risk.to_csv("accession_full_risk_data.csv", index=False)

    # Runs the script again on the test accession folder.
    # It will use existing fits.csv and full_risk_data.csv to update format_analysis.xlsx.
    iteration_three = subprocess.run(f"python {script_path} {accession_folder}", shell=True, stdout=subprocess.PIPE)
    msg = "\r\nUpdating the XML files in the FITS folder to match the files in the accession folder.\r\n" \
          "This will update fits.csv but will NOT update full_risk_data.csv from a previous script iteration.\r\n" \
          "Delete full_risk_data.csv before the script gets to that step for it to be remade with the new information.\r\n\r\n" \
          "Updating the analysis report using existing risk data.\r\n"
    compare_strings("Iteration_Message_3", iteration_three.stdout.decode("utf-8"), msg)

    # The next several code blocks makes dataframes with the expected values for each tab in format_analysis.xlsx.

    # Expected values for things that change (date and size and MD5 for XLSX and ZIP) are calculated
    # instead of using a constant for comparison. Ones used frequently are saved to variables.
    today = datetime.date.today().strftime('%Y-%m-%d')
    xlsx_kb = round(os.path.getsize(r"accession\disk1\data.xlsx") / 1000, 3)
    xlsx_mb = round(xlsx_kb / 1000, 3)
    zip_kb = round(os.path.getsize(r"accession\disk2\disk1backup.zip") / 1000, 3)
    three_zip_mb = round((os.path.getsize(r"accession\disk2\disk1backup.zip") / 1000 * 3) / 1000, 3)
    total_mb = df_risk["FITS_Size_KB"].sum()/1000

    # Expected values for the format subtotal.
    rows = [["empty", "Low Risk", 1, 10, 0, 0],
            ["Extensible Markup Language", "Low Risk", 1, 10, 0, 0],
            ["Office Open XML Workbook", "Low Risk", 1, 10, xlsx_mb, round((xlsx_mb / total_mb) * 100, 3)],
            ["Plain text", "Low Risk", 3, 30, 0.008, round((0.008 / total_mb) * 100, 3)],
            ["XLSX", "Low Risk", 1, 10, xlsx_mb, round((xlsx_mb / total_mb) * 100, 3)],
            ["ZIP Format", "Moderate Risk", 3, 30, three_zip_mb, round(((three_zip_mb) / total_mb) * 100, 3)]]
    column_names = ["FITS_Format_Name", "NARA_Risk Level", "File Count", "File %", "Size (MB)", "Size %"]
    df_format_subtotal_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the NARA risk subtotal.
    low_mb = round(df_risk[df_risk["NARA_Risk Level"] == "Low Risk"]["FITS_Size_KB"].sum() / 1000, 3)
    rows = [["Low Risk", 7, 70, low_mb, round((low_mb / total_mb) * 100, 3)],
            ["Moderate Risk", 3, 30, three_zip_mb, round((three_zip_mb / total_mb) * 100, 3)]]
    column_names = ["NARA_Risk Level", "File Count", "File %", "Size (MB)", "Size %"]
    df_nara_risk_subtotal_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the tech appraisal subtotal.
    rows = [["Format", "empty", 1, 10, 0, 0]]
    column_names = ["Technical_Appraisal", "FITS_Format_Name", "File Count", "File %", "Size (MB)", "Size %"]
    df_tech_appraisal_subtotal_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the other risk subtotal.
    rows = [["Archive format", "ZIP Format", 3, 30, three_zip_mb, round(((three_zip_mb) / total_mb) * 100, 3)]]
    column_names = ["Other_Risk", "FITS_Format_Name", "File Count", "File %", "Size (MB)", "Size %"]
    df_other_risk_subtotal_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the media subtotal.
    disk1_mb = round(df_risk[df_risk["FITS_File_Path"].str.contains(r"\\disk1\\")]["FITS_Size_KB"].sum() / 1000, 3)
    disk2_mb = round(df_risk[df_risk["FITS_File_Path"].str.contains(r"\\disk2\\")]["FITS_Size_KB"].sum() / 1000, 3)
    rows = [["disk1", 3, disk1_mb, 0, 0, 3, 0, 0, 0], ["disk2", 7, disk2_mb, 0, 3, 4, 0, 1, 3]]
    column_names = ["Media", "File Count", "Size (MB)", "NARA High Risk (File Count)",
                    "NARA Moderate Risk (File Count)", "NARA Low Risk (File Count)", "No NARA Match (File Count)",
                    "Technical Appraisal_Format (File Count)", "Other Risk Indicator (File Count)"]
    df_media_subtotal_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the NARA risk subset.
    rows = [[fr"{output}\accession\disk2\disk1backup.zip", "ZIP Format", 2, False, today, zip_kb, "XXXXXXXXXX",
             "Moderate Risk", "Retain but extract files from the container", "PRONOM", "Not for TA", "Archive format"],
            [fr"{output}\accession\disk2\disk1backup2.zip", "ZIP Format", 2, False, today, zip_kb, "XXXXXXXXXX",
             "Moderate Risk", "Retain but extract files from the container", "PRONOM", "Not for TA", "Archive format"],
            [fr"{output}\accession\disk2\disk1backup3.zip", "ZIP Format", 2, False, today, zip_kb, "XXXXXXXXXX",
             "Moderate Risk", "Retain but extract files from the container", "PRONOM", "Not for TA", "Archive format"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_Multiple_IDs",
                    "FITS_Date_Last_Modified", "FITS_Size_KB", "FITS_MD5", "NARA_Risk Level",
                    "NARA_Proposed Preservation Plan", "NARA_Match_Type", "Technical_Appraisal", "Other_Risk"]
    df_nara_risk_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the tech appraisal subset.
    rows = [[fr"{output}\accession\disk2\empty.txt", "empty", np.NaN, "file utility version 5.03",
             False, 0, np.NaN, "Low Risk", "Retain", "File Extension", "Format", "Not for Other"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_Identifying_Tool(s)",
                    "FITS_Multiple_IDs", "FITS_Size_KB", "FITS_Creating_Application", "NARA_Risk Level",
                    "NARA_Proposed Preservation Plan", "NARA_Match_Type", "Technical_Appraisal", "Other_Risk"]
    df_tech_appraisal_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the other risk subset.
    rows = [[fr"{output}\accession\disk2\disk1backup.zip", "ZIP Format", 2,
             "Droid version 6.4; file utility version 5.03; Exiftool version 11.54; ffident version 0.2; Tika version 1.21",
             False, zip_kb, "Moderate Risk", "Retain but extract files from the container", "PRONOM", "Not for TA",
             "Archive format"],
            [fr"{output}\accession\disk2\disk1backup2.zip", "ZIP Format", 2,
             "Droid version 6.4; file utility version 5.03; Exiftool version 11.54; ffident version 0.2; Tika version 1.21",
             False, zip_kb, "Moderate Risk", "Retain but extract files from the container", "PRONOM", "Not for TA",
             "Archive format"],
            [fr"{output}\accession\disk2\disk1backup3.zip", "ZIP Format", 2,
             "Droid version 6.4; file utility version 5.03; Exiftool version 11.54; ffident version 0.2; Tika version 1.21",
             False, zip_kb, "Moderate Risk", "Retain but extract files from the container", "PRONOM", "Not for TA",
             "Archive format"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_Identifying_Tool(s)",
                    "FITS_Multiple_IDs", "FITS_Size_KB", "NARA_Risk Level", "NARA_Proposed Preservation Plan",
                    "NARA_Match_Type", "Technical_Appraisal", "Other_Risk"]
    df_other_risk_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the multiple format identifications subset.
    rows = [[fr"{output}\accession\disk1\data.xlsx", "XLSX", np.NaN, np.NaN, "Exiftool version 11.54", True, today,
             xlsx_kb, "XXXXXXXXXX", "Microsoft Excel", "Low Risk", "Retain", "File Extension", "Not for TA",
             "Not for Other"],
            [fr"{output}\accession\disk1\data.xlsx", "Office Open XML Workbook", np.NaN, np.NaN, "Tika version 1.21",
             True, today, xlsx_kb, "XXXXXXXXXX", "Microsoft Excel", "Low Risk", "Retain", "File Extension",
             "Not for TA", "Not for Other"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_PUID",
                    "FITS_Identifying_Tool(s)", "FITS_Multiple_IDs", "FITS_Date_Last_Modified", "FITS_Size_KB",
                    "FITS_MD5", "FITS_Creating_Application", "NARA_Risk Level", "NARA_Proposed Preservation Plan",
                    "NARA_Match_Type", "Technical_Appraisal", "Other_Risk"]
    df_multiple_ids_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the duplicates subset.
    rows = [[fr"{output}\accession\disk2\disk1backup.zip", zip_kb, "XXXXXXXXXX"],
            [fr"{output}\accession\disk2\disk1backup2.zip", zip_kb, "XXXXXXXXXX"],
            [fr"{output}\accession\disk2\disk1backup3.zip", zip_kb, "XXXXXXXXXX"],
            [fr"{output}\accession\disk2\duplicate_file.txt", 3.6, "c0090e0840270f422e0c357b719e8857"],
            [fr"{output}\accession\disk1\duplicate_file.txt", 3.6, "c0090e0840270f422e0c357b719e8857"]]
    column_names = ["FITS_File_Path", "FITS_Size_KB", "FITS_MD5"]
    df_duplicates_expected = pd.DataFrame(rows, columns=column_names)

    # Expected values for the validation subset.
    rows = [[fr"{output}\accession\disk2\error.html", "Extensible Markup Language", 1, np.NaN, "Jhove version 1.20.1",
             False, today, 0.035, "e080b3394eaeba6b118ed15453e49a34", np.NaN, True, True,
             "Not able to determine type of end of line severity=info",
             "Low Risk", "Retain", "Format Name", "Not for TA", "Not for Other"]]
    column_names = ["FITS_File_Path", "FITS_Format_Name", "FITS_Format_Version", "FITS_PUID",
                    "FITS_Identifying_Tool(s)", "FITS_Multiple_IDs", "FITS_Date_Last_Modified", "FITS_Size_KB",
                    "FITS_MD5", "FITS_Creating_Application", "FITS_Valid", "FITS_Well-Formed", "FITS_Status_Message",
                    "NARA_Risk Level", "NARA_Proposed Preservation Plan", "NARA_Match_Type", "Technical_Appraisal",
                    "Other_Risk"]
    df_validation_expected = pd.DataFrame(rows, columns=column_names)

    # Makes a dataframe with the values from each tab in format_analysis.xlsx made by the script.
    # Provides a default MD5 for XLSX or ZIP files, since those have a different MD5 each time they are made.
    # If the df is all XLSX or ZIP, the column is filled with the default. Otherwise, it is filtered by format first.
    xlsx = pd.ExcelFile("accession_format-analysis.xlsx")
    df_format_subtotal = pd.read_excel(xlsx, "Format Subtotal")
    df_nara_risk_subtotal = pd.read_excel(xlsx, "NARA Risk Subtotal")
    df_tech_appraisal_subtotal = pd.read_excel(xlsx, "Tech Appraisal Subtotal")
    df_other_risk_subtotal = pd.read_excel(xlsx, "Other Risk Subtotal")
    df_media_subtotal = pd.read_excel(xlsx, "Media Subtotal")
    df_nara_risk = pd.read_excel(xlsx, "NARA Risk")
    df_nara_risk["FITS_MD5"] = "XXXXXXXXXX"
    df_tech_appraisal = pd.read_excel(xlsx, "For Technical Appraisal")
    df_other_risk = pd.read_excel(xlsx, "Other Risks")
    df_multiple_ids = pd.read_excel(xlsx, "Multiple Formats")
    df_multiple_ids["FITS_MD5"] = "XXXXXXXXXX"
    df_duplicates = pd.read_excel(xlsx, "Duplicates")
    replace_md5 = df_duplicates["FITS_File_Path"].str.endswith("zip")
    df_duplicates.loc[replace_md5, "FITS_MD5"] = "XXXXXXXXXX"
    df_validation = pd.read_excel(xlsx, "Validation")
    xlsx.close()

    # Compares the expected values to the actual script values.
    compare_dataframes("Iteration_Subtotal_Format", df_format_subtotal, df_format_subtotal_expected)
    compare_dataframes("Iteration_Subtotal_Tech_Appraisal", df_tech_appraisal_subtotal, df_tech_appraisal_subtotal_expected)
    compare_dataframes("Iteration_Subtotal_NARA_Risk", df_nara_risk_subtotal, df_nara_risk_subtotal_expected)
    compare_dataframes("Iteration_Subtotal_Other_Risk", df_other_risk_subtotal, df_other_risk_subtotal_expected)
    compare_dataframes("Iteration_Subtotal_Media", df_media_subtotal, df_media_subtotal_expected)
    compare_dataframes("Iteration_Subset_NARA_Risk", df_nara_risk, df_nara_risk_expected)
    compare_dataframes("Iteration_Subset_Tech_Appraisal", df_tech_appraisal, df_tech_appraisal_expected)
    compare_dataframes("Iteration_Subset_Other_Risk", df_other_risk, df_other_risk_expected)
    compare_dataframes("Iteration_Subset_Multiple_IDs", df_multiple_ids, df_multiple_ids_expected)
    compare_dataframes("Iteration_Subset_Duplicates", df_duplicates, df_duplicates_expected)
    compare_dataframes("Iteration_Subset_Validation", df_validation, df_validation_expected)

    # Deletes the test files.
    shutil.rmtree("accession")
    shutil.rmtree("accession_FITS")
    os.remove("accession_fits.csv")
    os.remove("accession_format-analysis.xlsx")
    os.remove("accession_full_risk_data.csv")


# Makes the output directory (the only script argument) the current directory for simpler paths when saving files.
# If the argument is missing or not a valid directory, ends the script.
try:
    output = sys.argv[1]
    os.chdir(output)
except (IndexError, FileNotFoundError):
    print("\nThe required script argument (output folder) is missing or incorrect.")
    sys.exit()

# Saves the path to the GitHub repo, which is used by a few of the tests.
# sys.argv[0] is the path to format_analysis_tests.py
repo = os.path.dirname(sys.argv[0])

# Makes counters for the number of passed and failed tests to summarize the results at the end.
PASSED_TESTS = 0
FAILED_TESTS = 0

# Calls each of the test functions, which either test a function in format_analysis.py or
# one of the analysis components, such as the duplicates subset or NARA risk subtotal.
# A summary of the test result is printed to the terminal and reports for failed tests are saved to the output folder.

# Tests for script inputs.
test_argument(repo)
test_check_configuration_function(repo)
test_csv_to_dataframe_function()
test_csv_to_dataframe_function_encoding_error()

# Tests for generating format information with FITS.
test_make_fits_xml()
test_fits_class_error()
test_update_fits_function()
test_make_fits_csv_function()
test_make_fits_csv_function_encoding_error()

# Tests for risk analysis of format information.
test_match_nara_risk_function()
test_match_technical_appraisal_function()
test_match_other_risk_function()
test_deduplicating_results_df()

# Tests for each subset.
test_nara_risk_subset()
test_multiple_ids_subset()
test_validation_subset()
test_tech_appraisal_subset()
test_other_risk_subset()
test_duplicates_subset()
test_empty_subset()

# Tests for each subtotal.
# Includes tests for the two (tech appraisal and other risk) where no files may meet that criteria.
test_format_subtotal()
test_nara_risk_subtotal()
test_tech_appraisal_subtotal()
test_tech_appraisal_subtotal_none()
test_other_risk_subtotal()
test_other_risk_subtotal_none()
test_media_subtotal_function()

# Test for running the complete script through the three iterations:
# Generating new data, using existing FITS data, and using existing risk data.
test_iteration(repo)

# Prints the number of tests which passed or failed.
print("\nThe testing script is complete. Results:")
if FAILED_TESTS == 0:
    print(f"\t* All {PASSED_TESTS} tests passed.")
else:
    print(f"\t* {PASSED_TESTS} passed.")
    print(f"\t* {FAILED_TESTS} failed. See output folder for logs of each failed test.")