# Re:cruiter 

<img src="https://github.com/AmateurAcademic/Re_cruiter/blob/master/Re_Cruiter_icon.png" width=20% height=20%>

*Find AI jobs with the help of AI!*

Re:cruiter is a prototyped end-to-end NLP recipe to automatically find job offers in your email, analyze and label them, and even reply back. [Check out Re:cruiter in action](https://www.linkedin.com/pulse/using-ai-analyze-job-recruitment-industry-bartmoss-st-clair/).

## Setup
With pip, setup your virtual environment and run `pip install -r requirements.txt`,

for anaconda use recruiter.yml,
`conda env create -f recruiter.yml`

The notebooks run in Jupyter Notebook/Lab.


## Dummy Data instructions
If you would like to try Re:cruiter out without scraping and classifiying your own data, you can use the dummy dataset, `files/dummy_data/job_email_examples.csv`. Skip over the first notebook `01_recruiter_collect_emails.ipynb`, the second notebook `02_recruiter_classifier.ipynb` can optionally also be skipped. 

## How to find job offers in your email: 01_recruiter_collect_emails.ipynb
To find emails from recruiters, you need to scrape your emails. MailHandler is a fully functional email scraper.

If you are using Gmail, you will be required to temporarily turn on [less secure access](https://support.google.com/accounts/answer/6010255). 

### 1.2 Email account
Run this codeblock and provide your email credentials.

### 1.3 Setup MailHandler
If you know roughly _when_ you were written by recruiters, you can add a cutoff date and it will only go back from today until this date. For example,

`MAIL_CUTOFF_DATE = "28-Feb-2020"`

Note the [abbreviated format](https://www.bydewey.com/monthdayabb.html) of the month. Otherwise leave it as `False`.


Supply the Mailer with the correct inbound and outbound servers, i.e. for Gmail:

`Mailer('scrape', inbound='imap.gmail.com', outbound='smtp.gmail.com', **credentials)`

### 1.4 Run MailHandler
MailHandler can be run on any folder in your email account. By default it is set to INBOX. 

`MailHandler.collect_emails(folder='INBOX', cutoff_date=MAIL_CUTOFF_DATE)`

When running MailHandler, it can take a while to scrape many emails. 
A maximum limit of emails can be set by passing it as a parameter to MailHandler.

`MailHandler.collect_emails(folder='INBOX', cutoff_date=MAIL_CUTOFF_DATE, limit=1000)`


The MailHandler also runs [langdetect](https://pypi.org/project/langdetect/) on the subjects of the scraped emails to label the emails by language. 

When MailHandler has successfully scraped all emails, the emails can be saved into a JSON file. For privacy reasons, the files that have personal data have been placed into `files/hide/` by default because the hide folder is ignored by GIT.

## Classifying the emails: 02_recruiter_classifier.ipynb
### 2.1 Loading and formatting the dataset
After loading the json file generated from MailHandler into a Pandas dataframe, i.e.

`test_set_df = pd.read_json('files/hide/scraped_mails.json')`

The date formatting is transformed into `YYYY, MM, DD`. If you think you have been sent the same emails several times based on the subject, you can drop the duplicates.

### 2.2 Classifiying the data
The classification of the emails is performed by a pre-trained model in [scikit-learn](https://pypi.org/project/scikit-learn/). The codeblocks in 2.0 result in a column ("predictions") appended to our recruiter dataframe.

### 2.3 Filter and ground truth results
Because the classifer only looks at the subject of emails to determine if an email is a recruiter email or not, it can be tricked by news letters and other emails that have titles such as "How to successfuly prepare for a data science interview in today's job market". 
Therefore, a list of domains has been given to filter out these false positives, i.e. 

`is_commercial = (test_set_df['domain'].isin(['linkedin.com', 'glassdoor.com', 'medium.com', 'quora.com', 'datacamp.com']))`

After filtering the false positives, the ground truthing can begin on both classes. To ground truth the results you will need [ipysheet](https://github.com/QuantStack/ipysheet) to display the results as a spreadsheet in your notebook and to check the boxes of incorrectly classified emails. 
(make small gif/video of clicking to ground truth)
Performing ground truthing on both the recruiter and non-recruiter emails ensures that our dataset is correct.

### 2.4 Export the ground truth dataset
The dataset is exported for the next notebook.


## Analyze and label the recruiter emails: 03_recruiter_NER.ipynb
The recruiter emails are analyzed and labeled for:

*job titles* (data scientist, CTO) and  *position types* (AI, tech, management) where a job title can have several position types.

*location* with SpaCy

*job requirement keyword*, *job requirements*, and *job requirement types*

meta data about the jobs from descriptions (title, location, duration, salary, experience)

and these results are used to filter job emails into interesting or uninteresting jobs.

### 3.1 Load the mail dataset
Load the ground truthed dataset exported as a CSV from the previous notebook as recruiter_df. The dummy dataset can also be used. 

### 3.2 Job type labeling on email subjects
We will want to find the *job titles* in the subject and classify them (this could also be done in the message itself).
Therefore, we will first search through the email subjects for the keywords in `job-types.json`. The keywords are ordered into job types (management, ai, dev, web), i.e.: 

"head of data science" is a combination of management and AI.

 I have also taken the liberty of scraping a lot of general job titles. If you want to search for other jobs by creating your own dictionary, that might be a good place to start with job titles:
 
 `files/job_titles/job-titles.json`
 
 The results are appended as columns ('jobTypes', 'jobTags') to the recruiter dataframe.


### 3.3 Clean subject texts and extraction location with SpaCy
A little bit of cleaning (i.e. remove 're:') is required to improve location tagging. Depending on the language of the email from MailHandler stored in the recruiter dataframe, it is recommeneded to stick with the same language model in [SpaCy](https://spacy.io/). By default, the English model is used (for installation of SpaCy, follow these [instructions](https://spacy.io/usage)).

The results are appeneded to the recruiter dataframe as a column ("location"). The SpaCy model used for named entity recognition can have issues detecting locations in subjects. This will be supplemented in 4.2. 


### Optional: Extract and clean requirements from message bullet points
If you want to analyze and create your own customized requirements based on your dataset, bullet points are a low hanging fruit for finding requirements. Many recruiter emails contain bullet points of the job requirements. From those, it is possible to get a good sample of requirements and turn that into a dictionary for the next step.


Note: message bullet points extraction is not supported in the dummy dataset. 


Run 4.0 if you want to make your own dictionary file to match requirements in emails instead of using the default one `requirement-types.json`
We need to get rough word counts of requirements, then clean the message_bullets with BeautifulSoup, as many emails are encoded in HTML.

Finally we will tokenize, remove stop words, and count the remaining keywords. Keep in mind, stop words will sometimes change words we don't want to like turn _kubernetes_ into _kupernete_. This count will only count single words, not phrases.


### 3.4 Get requirements from the email message contents
You can either use the default dictionary `requirement-types.json` or one you made based on the requirements from 4.0 to extract the requirements line by line from the whole message, not just the bullet points.

Note: If you are using the dummy dataset, skip the first two code blocks, the dummy dataset alredy has the column ('message_cleaned')

Optionally, there is a function called clean_requirements that you can throw in your RegEx to fix any issues that might occur in the requirements, such as in the example code, 

```def clean_requirements(requirement):
    if re.search('(build|develop|design)([^ ]* ){1,5}algorithm|algorithm design', requirement, re.I):
        requirement = re.sub('algorithm', 'research', requirement)
    return requirement
```

This matches a pattern in the requirements for "build/develop/design and algorithm/algorithm design" and replaces in that case "algorithm" with "research". Use as you wish.

Finally the results are appended as columns on the dataframe ("requirementTypes", "requirementKeywords", "requirements").

### 3.5 Extract meta job data from messages
By looking at the messages themselves, it can be seen that one or more of the following patterns often occurs:

role: (role)

salary: (salary)

title: (title)

duration: (duration)

education: (education)

Because of this we can extract this job meta data for further analysis. This is done in RegEx and can be easily changed, in my example I did it in German, ja:

`role_re = re.compile(r'(title|titel|roll?e|position)\s*:\s*(.+)', re.I)`

`location_re = re.compile(r'(Location|(?:stand)?ort):\s*(.+)', re.I)`

`duration_re = re.compile(r'(duration|dauer):\s*(.+)', re.I)`

`salary_re = re.compile(r'(gehalt|salary)::(?!\\r)\s*(.+)*', re.I)`

`education_re = re.compile(r'(education)::(?!\\r)\s*(.+)', re.I)`

Once the extraction is complete, the results are appeneded as columns in our recruiter dataframe, ("role", "location", "duration", "salary", "education"). For locations, all of the locations extracted are appended to the existing location column and overwrite the values from the named entity recognition, except where the location values extracted are NaN.

### 3.6 Sorting responses
In the final step of this notebook, we will perform a small analysis on the results of the recruiter dataframe and filter the results into interesting job offers and uninteresting.

I am personally interested in positions that combine management and AI, so I have filtered for these jobs. The results are exported into an ipysheet to be reviewed. If you are using Jupyter Lab, use "create new view for output".

Once the offers have been reviewed for interesting offers, the ipysheet is turned back into a dataframe and concatenated with the recruiter dataframe. All entries not marked as interesting are marked as uninteresting.

### 3.7 Export data

This dataframe is exported as a JSON file, 'processed_recruiter_mails.json'. We now have our complete analysis of the recruiter emails and are ready to reply.

## Reply to recruiters: 04_recruiter_send_emails.ipynb
To be a complete recipe, Re:cruiter should also send email responses back to recruiters using reply templates. The templates are located in `email_templates.py`. The templates are labled with reply criteria. The reply message itself can use slot values from `processed_recruiter_mails.json`.

For this example, the reply templates are labeled as English and German and whether you are interested in the position or not. Some slot filling can be used to personalize the message, .i.e. "Hi, #{firstname}" would get the first name value stored in `processed_recruiter_mails.json` in the key firstname.

Once you have set your templates up, it is strongly recommened to first test your templates before sending your replies to actual recruiters. Edit the `test_to_mail.json` file with your own email and domain to get an email sent to yourself as a preview. Load that into the notebook:

`MailHandler.load_emails('files/test_to_mail.json')` 

and run the whole notebook except:

`MailHandler.save_sent_emails()`. This saves the emails sent into a pickle file, to keep track of who you have already sent a message to. This should only be run when you send out real replies to recruiters.

Once you have properly tested your templates, its time to send out your replies from 'processed_recruiter_mails.json' and save it with `MailHandler.save_sent_emails()`.

Good luck finding the position that fits you! 
