<a name="top"></a>
# SLIC -  Salient Language In Context user guide
#### This guide covers account management as well as creating, publishing and collecting data from a SLIC language experiment.
---
## Table of contents

* [Signing up and Logging in](#signing_logging)
* [Managing and creating experiments](#exp_researcher)
    * [Creating an experiment](#exp_researcher_1)
    * [Editing](#exp_researcher_2)
    * [Publishing](#publishing)
    * [Results](#exp_researcher_3)
    * [Including SLIC tasks in other platforms](#unique_id)
* [Admin researcher functionalities](#admin)
    * [Manage users](#admin_1)
    * [Invitation links](#admin_2)
* [Data Processing and Visualisation](#processing)
    * [Using Praat to visualise output from the SLIC tool](#praat)
* [How to cite SLIC](#cite)

---
## <a name="signing_logging"></a> Signing up and Logging in
To access researcher functionalities you need to log in with an existing account. If you do not have your account yet, you can create one provided you [recieved an invitation](./contact_us) from an admin researcher.

##### To create an account:

1. Enter sign up page and enter your invitation code
  * __If you have an invitation link:__
      1. Follow the link you received, you should be now on 'Sign up' page.
      1. The last input 'Registration code' should be filled with your code.
  * __If you have an invitation code:__
      1. From the home page click on 'Sign up' ![Sign Up button](/static/images/sign_up_bt.png)  button located in top right corner.
      1. Scroll down and fill the 'Registration code' field with your code.
<br><br>
1. Fill the sign up form. You need to provide: Name, Country, Email, Password, Research Level. Other fields are optional. All this information can be changed later.

1. Click 'Sign up' button on the very bottom to finish registration. If there are any errors in the form, you will get the corresponding message. If successful, you should be logged in.

##### To log in:

1. From the home page click on 'Log in' ![Log In button](/static/images/log_in_bt.png) button located in top right corner.
1. Enter your email and correct password and click 'Log in' below the form.

---
## <a name="exp_researcher"></a> Managing and creating experiments
The experiment dashboard is accessed using the ![Experiments](/static/images/experiment_dashboard_button.png) button at the top of the screen when logged in. From here experiments can be managed, created and results can be accessed.
#### <a name="exp_researcher_1"> Creating an experiment
1. Click the ![New experiment](/static/images/new_experiment_button.png) button on the experiment dashboard.
2. Choose a name for the experiment and an optional description. Click "Create Experiment".  
  ![New experiment](/static/images/new_experiment.png)

**Once an experiment has been created it can be accessed and edited from the experiment dashboard at any time until it is published.**

#### <a name="exp_researcher_2"> Editing and publishing
An experiment can be edited from its experiment page, accessed by clicking its name in the experiment dashboard.

##### Title and description
1. From the experiment page click ![Edit](/static/images/edit_button.png).
2. Amend title and description.
3. Click "Edit Experiment".  
  ![Edit experiment](/static/images/edit_experiment.png)

##### Adding tasks
1. From the experiment page click one of the add buttons, e.g "Add question page".  
  ![Add task buttons](/static/images/add_task_button.png)
2. Choose a name for the new task and click the create button.  
  ![Add question task](/static/images/add_question_task.png)
3. The task will now be visible in the task list and can be accessed by clicking its name.  
  ![Task list](/static/images/experiment_tasks.png)

##### Editing tasks
* Clicking a task in the task list will take you to its task page.  
  ![Task page](/static/images/task_page.png)
* Task name can be changed by changing its name on the task page and clicking ![Change](/static/images/change_button.png).  

#### Task types
##### <a name="question_page"></a> Question page
A question page simply creates a form for the participant to fill in. It is useful for collecting data such as personal information. Note that the email address gathered on the first page of an experiment is for GDPR compliance purposes and will not be included in the experiment data, so you will need to ask for it again if it is required.

The following shows a question page from the point of view of the participant:
![Example question page](/static/images/example_questions.png)

* To add a question, click the relevant "Add question" button from the task page.  
  ![Add question buttons](/static/images/add_question_buttons.png)
* To change the prompt for a question, edit the prompt in the text field and click ![Change](/static/images/change_button.png).  
  ![Question prompt](/static/images/question_prompt.png)

###### Question types
There are 3 question types:

* **Text question**
  * A simple text field
* **Option question**
  * Dropdown box, Radio buttons (select one) or Checkboxes (select many).
  * To add an option, fill the text field in the options column with the option text and press add.  
    ![Add options](/static/images/add_options.png)
* **Rating Scale**
  * A numerical scale for a participant to rate something.
  * To change the scale text, change the "From" (Lowest) and "To" (Highest) fields in the options column and press "Change".
  * To change the number of options available to the participant, change the "Number of options" field in the options column and press "Change".  
    ![Change scale](/static/images/change_scale.png)

##### Audio sample
An Audio sample allows a participant to listen to, answer questions about, and react in real time to a provided audio sample.  

* To upload an audio file click browse, select the file on your device, and click "Upload audio".  
  ![Upload audio](/static/images/add_audio_file.png)
* To upload a transcript file click browse, select the file on your device, and click "Upload transcript".  
  ![Upload transcript](/static/images/add_transcript_file.png)
  * Transcript files must be in ELAN .eaf format.

###### Sample tasks

An audio sample can have tasks added to allow the participant to interact with the sample. The task types are as follows:  
  ![Audio task buttons](/static/images/add_audio_task_buttons.png)

* **Audio hearing**
  * An opportunity for the participant to listen to the audio sample.
* **Question page**
  * A page of questions about the sample. This task is set up in the same manner as an [experiment question page](#question_page).
* **Reaction task**
  * An opportunity for the participant to listen to the audio sample and click a button when they react to the provided prompt. After the sample is finished the participant is shown each clicked section and asked to justify their reaction.
  * To change the reaction prompt, click the reaction task on the sample task page, fill in the text field with the new reaction prompt and click "Change reaction prompt".  
  ![Change reaction prompt](/static/images/change_reaction.png)
  

  The following shows a reaction task from the point of view of a participant: 
  ![Example reaction task](/static/images/example_click_task.png)  

* It may be useful to include an easy calibration reaction task to measure response times of a participant and aid analysis of other reaction tasks. Clicking the ![This is a calibration task](/static/images/calibration.png) checkbox marks a sample as a calibration sample and disables click justification for reaction tasks.

#### <a name="publishing"> Publishing an experiment
To allow people to participate in an experiment it must first be published. An experiment can only be edited **before** being published and can only be completed by a participant **after** being published.  

**Publishing is irreversible. Once an expeiment has been published it cannot be edited**

To publish an experiment click ![Publish](/static/images/publish_button.png) on the experiment page and select "OK" on the confirmation popup.  
  ![Confirm publish](/static/images/publish_confirm.png)  

###### Publishing errors  
You may encounter warnings or errors when attempting to publish an experiment.  
  ![Publish errors](/static/images/publish_errors.png)  

  Errors appear when something major is wrong with your experiment, e.g. There is a listening task but you have not yet uploaded an audio file.  
  Warnings appear when something minor is wrong with your experiment, e.g. A question exists with the default name (New text question).  
  You must fix any errors before publishing an experiment, but warnings can be overridden with the ![publish_anyway](/static/images/publish_anyway.png) button.

#### <a name="exp_researcher_3"> Results
Once an experiment has been published results are available for download at any time.  
From an experiment page, basic completion statistics can be viewed for the current experiment.  
![Experiment stats](/static/images/experiment_stats.png)  
Current results for the experiment can be downloaded in Excel .xlsx format with the ![Download results](/static/images/download_results.png) button.  
The resulting document contains a sheet of responses for each question task and a sheet of click justifications for each reaction task.

#### <a name="unique_id"> Including SLIC tasks in other platforms
You may wish to include a SLIC task in a survey on a different platform. After completing an experiment, each participant will be shown a unique response ID which will be included in the results download.

![Unique response ID](/static/images/unique_id.png)

By providing participants with a link to a SLIC experiment and a field to insert their unique response id, results can be related between the two platforms.

---
## <a name="admin"> Admin researcher functionality

As a system admin you are given more options than normal researcher. Log in into your account, on the navigation bar you should see a drop-down button 'Admin tools' ![Admin tools](/static/images/admin_tools_bt.png). If you click on it you will see options: 'All users' and 'Invitations' ![Admin tools more](/static/images/admin_tools_more.png) . 

<br>
#### <a name="admin_2"> &nbsp;&nbsp;&nbsp; Manage users

![Admin tools more](/static/images/users.png)

From here you can see all registered reseachers. You can see some of their details in table but to see more, click on 'See more' button.
You can also set an account to be an admin account or remove account from the system. You cannot delete the last admin.



<br>
#### <a name="admin_1"> &nbsp;&nbsp;&nbsp; Invitations

![Invitations](/static/images/invitations.png)

When a researcher wants to register they need to provide a registration(/invitation) code

To create new invitation use the 'Create New Invitation' button in the bottom. Random code will be generated.

One can copy and paste this code into the form or alternatively follow the link which will automatically fill the required form input.

---
## <a name="processing"> Data Processing and Visualisation

#### <a name="praat"> Using Praat to visualise output from the SLIC tool

The Praat program can be used to prepare visualisations of the times of the reactions captured by the SLIC tool, in dynamic editor windows and as static graphics:

* makeReactionRealtiers.praat (to inspect reactions in dynamic editor windows): [package](https://github.com/walkergareth/praat/blob/main/makeReactionRealTiers.praat), [documentation](https://github.com/walkergareth/praat/blob/main/makeReactionRealTiers.pdf)

* drawReactionData.praat (to prepare static graphics): [package](https://github.com/walkergareth/praat/blob/main/visreps/drawReactionData.praat), [documentation](https://github.com/walkergareth/praat/blob/main/visreps/drawReactionData.pdf)

* makeReactionTextGrids.praat (to create TextGrids containing click and comment data, to be viewed in dynamic editor windows): [package](https://github.com/walkergareth/praat/blob/main/makeReactionTextGrids.praat), [documentation](https://github.com/walkergareth/praat/blob/main/makeReactionTextGrids.pdf)

---
## <a name="cite"></a> How to cite SLIC

SLIC is free to use for non-commercial research purposes. If you use SLIC to collect data, you must cite the following paper in any publication, presentation, report, or other research output:

> Montgomery, Chris, Gareth Walker and Harry Woods. 2025. Salient Language in Context (SLIC): a web app for collecting real-time attention data in response to audio samples. *Linguistics Vanguard* 11(1): 397-406. https://doi.org/10.1515/lingvan-2025-0028

[Back to top](#top)
