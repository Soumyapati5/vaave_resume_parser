import sys
from pdfminer.layout import LAParams,LTTextLine, LTTextBoxHorizontal,LTTextContainer, LTChar, LAParams
from pdfminer.high_level import extract_text, extract_pages
import re
import json
import unicodedata
import streamlit as st
from geotext import GeoText


resume = st.file_uploader("Upload your resume (pdf)", type=["pdf"])

### this function return text and font size in list of list
def extract_text_and_sizes(pdf_path):
    extract_data = []
    # with open(pdf_path, 'rb') as fp:
    laparams = LAParams()
    for page_layout in extract_pages(pdf_path, laparams=laparams):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                font_size = None
                text = ''
                if isinstance(element._objs[0], LTChar):
                    font_size = element._objs[0].size
                    text = element.get_text().strip()
                else:
                    for text_line in element:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                if font_size is None:
                                    font_size = character.size
                                text += character.get_text()
                extract_data.append([font_size, text])
    return extract_data

def extract_education_details(lines):
    education_started = False
    education_lines = []
    for line in lines:   ### this extract is Education is in Resume
        text = str(line[1]).strip()
        font_size = float(line[0])
        if education_started:
            education_lines.append((font_size, text))
        elif font_size == 15.75 and "Education" in text:
            education_started = True
            education_lines.append((font_size, text))
        
    return education_lines

### this is clean and mearging similar sentence
def mraeg_education_details(lines):
    education_started = False
    education_lines = []
    for line in lines:
        text = str(line[1]).strip()
        font_size = float(line[0])
        if education_started:
            if education_lines and abs(font_size - education_lines[-1][0]) < 1.0:
                # If the font size of the current line is close to the font size of the previous line, merge the lines
                education_lines[-1] = (education_lines[-1][0], education_lines[-1][1] + ' ' + text)
            else:
                # Otherwise, add the current line to the list
                education_lines.append((font_size, text))
        elif font_size == 15.75 and "Education" in text:
            education_started = True
            education_lines.append((font_size, text))
        
    return education_lines

### this is final function for extracting Eduction in zip format
def extract_education(education_data):
    education = []
    institutes = education_data[1:len(education_data):2]
    courses = education_data[2:len(education_data):2]

    for i in range(len(institutes)):
        institute = institutes[i]
        course = courses[i]
        year_range_match = re.search(r'\((.*?)\)', course)
        if year_range_match:
            year_range = year_range_match.group(1)
            course = course.replace('({})'.format(year_range), '').strip()
            if '-' in year_range:
                start_year, end_year = year_range.split('-')
            else:
                start_year = end_year = year_range.strip()
            education.append({"institute": institute, "course": course, "start_year": start_year.strip(), "end_year": end_year.strip()})
        else:
            education.append({"institute":institute, "course":course, "start_year":'',  "end_year":''})

    return education

### this function remove some period of work in experience section
def remove_period_exp(lst):
    regex = r"(?<!\d)(\d+)\s*(years|year)?\s*(\d+)?\s*(months|month)?(?!\sdays)"
    result = []
    for s in lst:
        if not re.search(regex, s) or ("(" in s and "-" in s):
            result.append(s)
    return result

### this function extract Expeience
def extract_experience(text):
    experiences = []
    i = 0
    last_company_name = ""
    while i < len(text):
        if "Experience" in text[i]:
            j = i + 1
            while j < len(text) and ("Education" not in text[j] and j != len(text)-1):
                date_match = re.search(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\s*-\s*(?:\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\bPresent)\b|\d+\s+months", text[j])
                if date_match:
                    company_name = text[j-2].strip()
                    if "(" in company_name and ")" in company_name and "-" in company_name and any(char.isdigit() for char in company_name):
                        company_name = last_company_name
                    else:
                        last_company_name = company_name
                    position = text[j-1].strip()
                    date = date_match.group()
                    if "-" in date:
                        start_date, end_date = date.split("-")
                    else:
                        start_date = date
                        end_date = "Present"

                    # Check if there is any extra text after stripping the date
                    description = text[j].strip()
                    if len(description) >= 25:
                        # Remove the date from the description
                        description = re.sub(date, "", description)
                        # Remove any year/month/days information from the description
                        description = re.sub(r"(?<!\d)\(\s*(\d+)\s*(years|year)?\s*(\d+)?\s*(months|month)?\s*\)(?!\sdays)", "", description)
                        extra_text = description.strip()
                    else:
                        extra_text = ""
                        
                    # Check if any of the first three words are a location
                    location_words = []
                    locat = ""
                    if extra_text:
                        first_three_words = extra_text.split()[:3]
                        if len(first_three_words) > 1 and (GeoText(first_three_words[0]).cities) and (GeoText(first_three_words[-1]).countries):
                            location_words = first_three_words
                        else:
                            for word in first_three_words:
                                if GeoText(word).cities or GeoText(word).countries or word in ['Area', 'Area,' , "Bengaluru", 'Bengaluru,', 'Karnataka,', 'Telangana', 'Telangana,', 'Punjab,', 'Haryana,','Madhya' ,'Pradesh,']:
                                    location_words.append(word)

                        # Join the location words into a string
                        locat = " ".join(location_words)

                        # Strip the location from the text
                        extra_text = extra_text.replace(locat, "").strip()

                    experience = {
                        "company_name": company_name,
                        "position": position,
                        "start_date": start_date,
                        "end_date": end_date,
                        "company_location": locat,
                        "description": extra_text
                    }
                    experiences.append(experience)
                j += 1
            i = j
        else:
            i += 1

    return experiences

### this is the main function that returns output
def resume_parser(resume):
    text_and_size = extract_text_and_sizes(resume)
    my_list = [(font_size,text) for font_size,text in text_and_size if font_size != 8.999999999999998 and text != ""]


    alld = {
        "name": "",
        "profile_summary": "",
        "location": "",
        "linkedin" : "",
        "email": "",
        "phone":"",
        "profile_basic": "",
        "summary" : "",
        "education" : "",
        "experience" : ""
        }
    

    result = {}
    for i in range(len(my_list)-1):
        current_size, current_text = my_list[i]
        next_size, next_text = my_list[i+1]
        if current_size == 13 and next_size in [10.5, 11]:
            key = current_text.strip().lower().replace(' ', '_') ### Changing naming convention of key
            value = []
            j = i+1
            while j < len(my_list) and my_list[j][0] in [10.5, 11]:
                value.append(my_list[j][1].strip())
                j += 1
            ### If condition to exclude 'Contact' key value
            if key != 'contact':
                result[key] = value
    alld["profile_basic"] = result

    edu = extract_education_details(my_list)
    final_edu = mraeg_education_details(edu)
    edu_last = []
    for i , j in final_edu:
        normalized_text = unicodedata.normalize('NFKD', j).encode('ASCII', 'ignore').decode()
        edu_last.append(normalized_text)

    educat = extract_education(edu_last)
    alld["education"] = educat

    text_sizes = []


    for page_layout in extract_pages(resume):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        font_size = text_line._objs[0].size
                        text = text_line.get_text().strip()
                        if text:
                            text_sizes.append((text, font_size))
    ### It remove unwanted text
    filtered_data = [(text, fontsize) for (text, fontsize) in text_sizes if fontsize != 8.999999999999998 and text != ""]

    merged_list = []
    prev_size = None
    for item in filtered_data:
        text, size = item
        if prev_size is not None and abs(size - prev_size) < 0.1:
            merged_list[-1] = (merged_list[-1][0] + ' ' + text, size)
        else:
            merged_list.append(item)
        prev_size = size

    name = None
    profile_summary = ""
    location = None

    for i in range(len(filtered_data)):
        if filtered_data[i][1] == 26.0:
            name = filtered_data[i][0]
        elif filtered_data[i][1] == 12.0 and name is not None and location is None:
            profile_summary += filtered_data[i][0] + " "
        elif filtered_data[i][1] != 12.0 and name is not None and location is None:
            location = filtered_data[i-1][0]
            break

    if name == location:
        location = ""

    # Remove the location from profile_summary
    if location is not None:
        profile_summary = profile_summary.replace(location, "")

    alld["name"]= name
    alld["profile_summary"]= profile_summary
    alld["location"]= location

    filtered_data = [(text, fontsize) for (text, fontsize) in merged_list if fontsize != 8.999999999999998 and text != ""]

    exp_last = []
    for text, font_size in merged_list:
        normalized_text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
        exp_last.append(normalized_text)

    linkdin = re.findall(r"www\.linkedin\.com\/[^\(]+",str(exp_last))

    for i in range(len(linkdin)):
        linkdin[i] = linkdin[i].replace(" ", "")
    for i in linkdin:
        if len(i) >= 80:
            print("Plesse inpute a valid resume format")
        else:
            alld["linkedin"] = i  # store the first LinkedIn link found
            break

    email = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(exp_last))
    alld["email"] = email
    phone = re.findall(r"(?:\+91\s)?\d{10}", str(exp_last))
    alld["phone"] = phone

    exp_last2 = []
    for text, font_size in filtered_data:
        normalized_text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
        exp_last2.append((normalized_text, font_size))

    merged_list2 = []
    prev_size = None
    for item in exp_last2:
        text, size = item
        if prev_size is not None and abs(size - prev_size) < 0.1:
            merged_list2[-1] = (merged_list2[-1][0] + ' ' + text, size)
        else:
            merged_list2.append(item)
        prev_size = size

    exp_last_text = [text for text, _ in merged_list2]
    final_text = remove_period_exp(exp_last_text)
    experience = extract_experience(final_text)
    alld["experience"] = experience

    try:
        summary_index = next((i for i, (text, font_size) in enumerate(merged_list) if text == "Summary" and font_size == 15.75), -1)

    # If the summary is found, extract it and store it in the dictionary
        if summary_index != -1 and summary_index + 1 < len(merged_list) and merged_list[summary_index + 1][1] == 12.0:
            profile_summary = merged_list[summary_index + 1][0]
            alld["summary"] = profile_summary
        else:
            # If summary text not match then look for "Experience" or "Education"
            experience_index = next((i for i, x in enumerate(final_text) if "Experience" in x), -1)
            education_index = next((i for i, x in enumerate(final_text) if "Education" in x), -1)
        
            # If "Experience" is found, it extract text between "Summary" and "Experience"
            if experience_index != -1:
                for i in range(summary_index + 1, experience_index):
                    if len(final_text[i]) > 100:
                        alld["summary"] += final_text[i] + " "
            
            # If "Education" is found, extract text between "Summary" and "Education"
            elif education_index != -1:
                for i in range(summary_index + 1, education_index):
                    if len(final_text[i]) > 100:
                        alld["summary"] += final_text[i] + " "
        
        # If neither "Experience" nor "Education" is found, set "Summary" to an empty string
            else:
                alld["summary"] = ""

    except StopIteration:
        alld["summary"] = ""

    parsed_data = json.dumps(alld, indent=4, ensure_ascii=False)

    return parsed_data

if st.button("Parse"):
    if resume is not None:
        # Parsed_data = parse_resume(resume)
        try:
            output = resume_parser(resume)
        except FileNotFoundError:
            st.write("Error: file not found.")
        except ValueError:
            st.write("Error: invalid input. Please input a valid LinkedIn URL or path to a PDF resume.")
        except IndexError:
            st.write("Error: It works for Linkedin Resumes.")
        except Exception as e:
            st.write("Error: {}".format(str(e)))
        else:
            st.success("Information Extracted")
            st.json(output)
    else:
        st.error("Please upload a valid resume")