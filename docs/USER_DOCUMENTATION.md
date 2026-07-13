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

---
## <a name="signing_logging"></a> Signing up and Logging in
To access researcher functionalities you need to log in with an existing account. If you do not have your account yet, you can create one provided you [recieved an invitation](./contact_us) from an admin researcher.

##### To create an account:

1. Enter sign up page and enter your invitation code
  * __If you have an invitation link:__
      1. Follow the link you received, you should be now on 'Sign up' page.
      1. The last input 'Registration code' should be filled with your code.
  * __If you have an invitation code:__
      1. From the home page click on 'Sign up' ![Sign Up button](/images/sign_up_bt.png)  button located in top right corner.
      1. Scroll down and fill the 'Registration code' field with your code.
<br><br>
1. Fill the sign up form. You need to provide: Name, Country, Email, Password, Research Level. Other fields are optional. All this information can be changed later.

1. Click 'Sign up' button on the very bottom to finish registration. If there are any errors in the form, you will get the corresponding message. If successful, you should be logged in.

##### To log in:

1. From the home page click on 'Log in' ![Log In button](/images/log_in_bt.png) button located in top right corner.
1. Enter your email and correct password and click 'Log in' below the form.

---
## <a name="exp_researcher"></a> Managing and creating experiments
The experiment dashboard is accessed using the ![Experiments](/images/experiment_dashboard_button.png) button at the top of the screen when logged in. From here experiments can be managed, created and results can be accessed.
#### <a name="exp_researcher_1"> Creating an experiment
1. Click the ![New experiment](/images/new_experiment_button.png) button on the experiment dashboard.
2. Choose a name for the experiment and an optional description. Click "Create Experiment".  
  ![New experiment](/images/new_experiment.png)

**Once an experiment has been created it can be accessed and edited from the experiment dashboard at any time until it is published.**

#### <a name="exp_researcher_2"> Editing and publishing
An experiment can be edited from its experiment page, accessed by clicking its name in the experiment dashboard.

##### Title and description
1. From the experiment page click ![Edit](/images/edit_button.png).
2. Amend title and description.
3. Click "Edit Experiment".  
  ![Edit experiment](/images/edit_experiment.png)

##### Adding tasks
1. From the experiment page click one of the add buttons, e.g "Add question page".  
  ![Add task buttons](/images/add_task_button.png)
2. Choose a name for the new task and click the create button.  
  ![Add question task](/images/add_question_task.png)
3. The task will now be visible in the task list and can be accessed by clicking its name.  
  ![Task list](/images/experiment_tasks.png)

##### Editing tasks
* Clicking a task in the task list will take you to its task page.  
  ![Task page](/images/task_page.png)
* Task name can be changed by changing its name on the task page and clicking ![Change](/images/change_button.png).  

#### Task types
##### <a name="question_page"></a> Question page
A question page simply creates a form for the participant to fill in. It is useful for collecting data such as personal information. Note that the email address gathered on the first page of an experiment is for GDPR compliance purposes and will not be included in the experiment data, so you will need to ask for it again if it is required.

The following shows a question page from the point of view of the participant:
![Example question page](/images/example_questions.png)

* To add a question, click the relevant "Add question" button from the task page.  
  ![Add question buttons](/images/add_question_buttons.png)
* To change the prompt for a question, edit the prompt in the text field and click ![Change](/images/change_button.png).  
  ![Question prompt](/images/question_prompt.png)

###### Question types
There are 3 question types:

* **Text question**
  * A simple text field
* **Option question**
  * Dropdown box, Radio buttons (select one) or Checkboxes (select many).
  * To add an option, fill the text field in the options column with the option text and press add.  
    ![Add options](/images/add_options.png)
* **Rating Scale**
  * A numerical scale for a participant to rate something.
  * To change the scale text, change the "From" (Lowest) and "To" (Highest) fields in the options column and press "Change".
  * To change the number of options available to the participant, change the "Number of options" field in the options column and press "Change".  
    ![Change scale](/images/change_scale.png)

##### Audio sample
An Audio sample allows a participant to listen to, answer questions about, and react in real time to a provided audio sample.  

* To upload an audio file click browse, select the file on your device, and click "Upload audio".  
  ![Upload audio](/images/add_audio_file.png)
* To upload a transcript file click browse, select the file on your device, and click "Upload transcript".  
  ![Upload transcript](/images/add_transcript_file.png)
  * Transcript files must be in ELAN .eaf format.

###### Sample tasks

An audio sample can have tasks added to allow the participant to interact with the sample. The task types are as follows:  
  ![Audio task buttons](/images/add_audio_task_buttons.png)

* **Audio hearing**
  * An opportunity for the participant to listen to the audio sample.
* **Question page**
  * A page of questions about the sample. This task is set up in the same manner as an [experiment question page](#question_page).
* **Reaction task**
  * An opportunity for the participant to listen to the audio sample and click a button when they react to the provided prompt. After the sample is finished the participant is shown each clicked section and asked to justify their reaction.
  * To change the reaction prompt, click the reaction task on the sample task page, fill in the text field with the new reaction prompt and click "Change reaction prompt".  
  ![Change reaction prompt](/images/change_reaction.png)
  

  The following shows a reaction task from the point of view of a participant: 
  ![Example reaction task](/images/example_click_task.png)  

* It may be useful to include an easy calibration reaction task to measure response times of a participant and aid analysis of other reaction tasks. Clicking the ![This is a calibration task](/images/calibration.png) checkbox marks a sample as a calibration sample and disables click justification for reaction tasks.

#### <a name="publishing"> Publishing an experiment
To allow people to participate in an experiment it must first be published. An experiment can only be edited **before** being published and can only be completed by a participant **after** being published.  

**Publishing is irreversible. Once an expeiment has been published it cannot be edited**

To publish an experiment click ![Publish](/images/publish_button.png) on the experiment page and select "OK" on the confirmation popup.  
  ![Confirm publish](/images/publish_confirm.png)  

###### Publishing errors  
You may encounter warnings or errors when attempting to publish an experiment.  
  ![Publish errors](/images/publish_errors.png)  

  Errors appear when something major is wrong with your experiment, e.g. There is a listening task but you have not yet uploaded an audio file.  
  Warnings appear when something minor is wrong with your experiment, e.g. A question exists with the default name (New text question).  
  You must fix any errors before publishing an experiment, but warnings can be overridden with the ![publish_anyway](/images/publish_anyway.png) button.

#### <a name="exp_researcher_3"> Results
Once an experiment has been published results are available for download at any time.  
From an experiment page, basic completion statistics can be viewed for the current experiment.  
![Experiment stats](/images/experiment_stats.png)  
Current results for the experiment can be downloaded in Excel .xlsx format with the ![Download results](/images/download_results.png) button.  
The resulting document contains a sheet of responses for each question task and a sheet of click justifications for each reaction task.

#### <a name="unique_id"> Including SLIC tasks in other platforms
You may wish to include a SLIC task in a survey on a different platform. After completing an experiment, each participant will be shown a unique response ID which will be included in the results download.

![Unique response ID](/images/unique_id.png)

By providing participants with a link to a SLIC experiment and a field to insert their unique response id, results can be related between the two platforms.

---
## <a name="admin"> Admin researcher functionality

As a system admin you are given more options than normal researcher. Log in into your account, on the navigation bar you should see a drop-down button 'Admin tools' ![Admin tools](/images/admin_tools_bt.png). If you click on it you will see options: 'All users' and 'Invitations' ![Admin tools more](/images/admin_tools_more.png) . 

<br>
#### <a name="admin_2"> &nbsp;&nbsp;&nbsp; Manage users

![Admin tools more](/images/users.png)

From here you can see all registered reseachers. You can see some of their details in table but to see more, click on 'See more' button.
You can also set an account to be an admin account or remove account from the system. You cannot delete the last admin.



<br>
#### <a name="admin_1"> &nbsp;&nbsp;&nbsp; Invitations

![Invitations](/images/invitations.png)

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

[Back to top](#top)
