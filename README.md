# SundayTicketScheduler
Simple TKinter app to automatically replace EPG and TuneAll for COM3000 systems on sunday

Known Issues:
    -   When 'submitting' either EPG or TuneAll or Both, the selenium webdriver (edge used currently) causes empty command prompts to appear when their thread workers begin.



Process to manuall use this tool:
1.  Define the COM Card IP on the left side of the app.
    a.  This should be where the active EPG exists. TuneAll can happen on any card. Default is 192.168.3.18.
2.  Copy/Paste the EPG's into their corresponding boxes, or open from a stored text file using the 'Open TXT File' button.
    a.  'Everyday' refers to normal use. 
    b.  'Sunday Ticket' refers to Sundays EPG only.
3.  Select 'TuneAll' from the section selector at the top.
4.  Copy/Paste the TuneAll information being changed, or open from a stored text file using the 'Open TXT File' button.
    a.  'Everyday' refers to normal use. 
    b.  'Sunday Ticket' refers to Sundays EPG only.
    c.  Our experience shows that a user only need define the tuners being modified in the TuneAll -- this will also shorten the time taken to alter them.
5.  Use the selection on the left side to choose 'Everyday' or 'Sunday Ticket'.
    a.  This selector chooses which EPG/TuneAll box to deploy to the defined IP address
6.  Press whichever button that is desired to deploy.
    a. Submit buttons will 'grey out' when the deployment is being processed. 
        i.  Submit all greys all buttons
        ii. Submit EPG/Submit TuneAll greys out their corresponding buttons, and the 'Submit All' button.


Process to use the automatic scheulder:
1.  Steps 1 through 4 must be followed before using the automatic scheduler.
2.  For best results, ensure the system time is correctly set based upon the location.
    a.  The app displays current system time in the upper left of the app.
3.  Toggle ON the 'Automatically submit on Sunday' in the lower left corner of the app.
    NOTE: This will automatically run the 'Submit All' process for the current time. If it's not sunday, then 'Everyday EPG' and 'Everyday TuneAll' will submit. If it is Sunday, then the Sunday Ticket equivalents will submit.

How the scheduler executes:
-   When the day switches to say 'Sunday', will 'Submit All' the Sunday Ticket EPG and Sunday Ticket TuneAll.
-   When the day switches away from 'Sunday', it will 'Submit All' the Everyday EPG and Everyday TuneAll. This will execute only once.
-   When 'Automatically submit on Sunday' is enabled, the user will not be able to fully close the software without manually closing the window in the taskbar, or other 
    more extreme means. This is to ensure the scheduler remains active.


