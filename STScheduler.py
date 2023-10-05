import sys
import os
import customtkinter
import threading
import logging
import tkinter as tk
from tkinter import filedialog
from time import strftime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from subprocess import CREATE_NO_WINDOW

#https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

appdata_dir = os.getenv('APPDATA')
log_file_path = os.path.join(appdata_dir, "SundayTicketScheduler.log")

logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
app_logger = logging.getLogger("app")

webdriver_logger = logging.getLogger("selenium.webdriver")
webdriver_logger.setLevel(logging.INFO)
webdriver_logger.addHandler(logging.FileHandler(log_file_path))

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.automation_thread_epg = None
        self.automation_thread_tuneall = None
        self.button_trigger = False
        self.event_status = None
        self.weekday_runtime = True
        self.sunday_runtime = True

        # configure window
        self.title("Sunday Ticket COM3000 Deployment Tool")
        self.geometry(f"{1200}x{720}")
        self.iconbitmap(resource_path('.\\assets\\icon.ico'))
              
        # configure grid layout (4x4)
        self.grid_rowconfigure(0, weight=1)  # Allocate extra vertical space to the tabview area
        self.grid_columnconfigure(1, weight=1)  # Allocate extra horizontal space to the tabview area


        ##SideBar

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(12, weight=1) # If modifying items on sidebar (adding) make sure to increment by 1

        # Sidebar 'Main Label' and clock
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Sunday Ticket Settings", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.clock_lbl = customtkinter.CTkLabel(self.sidebar_frame, font=("Arial", 16))
        self.clock_lbl.grid(row=1, column=0, padx=20, pady=10)
        self.time()

        # Sidebar selector for which item to submit
        self.selector_label = customtkinter.CTkLabel(self.sidebar_frame, text="Which day to submit?", anchor="w")
        self.selector_label.grid(row=3, column=0, padx=2, pady=(0, 20))
        self.selector_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=['Everyday', 'Sunday Ticket'])
        self.selector_optionemenu.grid(row=2, column=0, padx=2, pady=(10, 0))
        
        # Sidebar Buttons to submit
        self.sidebar_button_0 = customtkinter.CTkButton(self.sidebar_frame, text="Submit All", command=self.submit_both_button)
        self.sidebar_button_0.grid(row=4, column=0, padx=20, pady=10)
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Submit EPG", command=self.submit_epg_button)
        self.sidebar_button_1.grid(row=5, column=0, padx=20, pady=2)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="Submit TuneAll", command=self.submit_tuneall_button)
        self.sidebar_button_2.grid(row=6, column=0, padx=20, pady=2)
        
        # Sidebar IP Entry (A)
        self.sidebar_entry_label = customtkinter.CTkLabel(self.sidebar_frame, text="COM Card IP (A):", anchor="w")
        self.sidebar_entry_label.grid(row=7, column=0, padx=0, pady=(0, 0))
        self.sidebar_entry = customtkinter.CTkEntry(self.sidebar_frame, justify="center")
        self.sidebar_entry.grid(row=8, column=0, padx=1, pady=5)

        # Sidebar IP Entry (B)
        self.sidebar_entry_label_b = customtkinter.CTkLabel(self.sidebar_frame, text="COM Card IP (B):", anchor="w")
        self.sidebar_entry_label_b.grid(row=9, column=0, padx=0, pady=(0, 0))
        self.sidebar_entry_b = customtkinter.CTkEntry(self.sidebar_frame, justify="center")
        self.sidebar_entry_b.grid(row=10, column=0, padx=1, pady=0)

        # button to test if ip entry B is empty or not
        # self.sidebar_test_button = customtkinter.CTkButton(self.sidebar_frame, text="TEST IP", command=self.test_ip_b)
        # self.sidebar_test_button.grid(row=11, column=0)

        #sidebar scaling selector
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=20, column=0, padx=2, pady=(5, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%", "130%", "140%", "150%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=21, column=0, padx=2, pady=(5, 0))

        # Switch to enable/disable auto_submit
        self.sidebar_switch = customtkinter.CTkSwitch(self.sidebar_frame, text="Automatically submit on Sunday", command=self.scheduler,
                                                     onvalue='On', offvalue='Off')
        self.sidebar_switch.grid(row=22, column=0, padx=20, pady=5)

        ##MainWindow

        # create tabview
        self.tabview = customtkinter.CTkTabview(self, width=500)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, rowspan=4, sticky="nsew")        

        # EPG(A) tabview and corresponding textboxes
        self.epg_tab_frame = self.tabview.add('EPG(A)')
        self.epg_tab_frame.columnconfigure(1, weight=1)
        self.epg_tab_frame.columnconfigure(2, weight=1)
        self.epg_tab_frame.rowconfigure(1, weight=1)
        label_1 = customtkinter.CTkLabel(self.epg_tab_frame, text="Everyday EPG(A)", font=("Arial", 12))
        label_1.grid(row=0, column=0, pady=(20, 0), columnspan=2)
        self.textbox_1 = customtkinter.CTkTextbox(self.epg_tab_frame)
        self.textbox_1.grid(row=1, column=1, padx=(20, 10), pady=(20, 0), sticky="nsew")
        
        label_2 = customtkinter.CTkLabel(self.epg_tab_frame, text="Sunday Ticket EPG(A)", font=("Arial", 12))
        label_2.grid(row=0, column=2, pady=(20, 0), columnspan=2)
        self.textbox_2 = customtkinter.CTkTextbox(self.epg_tab_frame)
        self.textbox_2.grid(row=1, column=2, padx=(10, 20), pady=(20, 0), sticky="nsew")

        #Open .txt file to input to textfields
        self.openEverydayEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Open TXT File", command=self.upload_ED_Epg)
        self.openEverydayEpg.grid(row=2, column=0, pady=(10, 0), columnspan=2)
        self.openSundayTicketEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Open TXT File", command=self.upload_ST_Epg)
        self.openSundayTicketEpg.grid(row=2, column=2, pady=(10, 0), columnspan=2)

        #Submit textfields
        self.submitEdEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Save Everyday EPG(A)", command=self.save_epg_ed)
        self.submitEdEpg.grid(row=3, column=0, pady=(10, 0), columnspan=2)
        self.submitStEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Save Sunday Ticket EPG(A)", command=self.save_epg_st)
        self.submitStEpg.grid(row=3, column=2, pady=(10, 0), columnspan=2)

        # EPG(B) tabview and corresponding textboxes
        self.epg_tab_frame = self.tabview.add('EPG(B)')
        self.epg_tab_frame.columnconfigure(1, weight=1)
        self.epg_tab_frame.columnconfigure(2, weight=1)
        self.epg_tab_frame.rowconfigure(1, weight=1)
        label_5 = customtkinter.CTkLabel(self.epg_tab_frame, text="Everyday EPG(B)", font=("Arial", 12))
        label_5.grid(row=0, column=0, pady=(20, 0), columnspan=2)
        self.textbox_5 = customtkinter.CTkTextbox(self.epg_tab_frame)
        self.textbox_5.grid(row=1, column=1, padx=(20, 10), pady=(20, 0), sticky="nsew")
        
        label_6 = customtkinter.CTkLabel(self.epg_tab_frame, text="Sunday Ticket EPG(B)", font=("Arial", 12))
        label_6.grid(row=0, column=2, pady=(20, 0), columnspan=2)
        self.textbox_6 = customtkinter.CTkTextbox(self.epg_tab_frame)
        self.textbox_6.grid(row=1, column=2, padx=(10, 20), pady=(20, 0), sticky="nsew")

        #Open .txt file to input to textfields
        self.openEverydayEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Open TXT File", command=self.upload_ed_epg_b)
        self.openEverydayEpg.grid(row=2, column=0, pady=(10, 0), columnspan=2)
        self.openSundayTicketEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Open TXT File", command=self.upload_st_epg_b)
        self.openSundayTicketEpg.grid(row=2, column=2, pady=(10, 0), columnspan=2)

        #Submit textfields
        self.submitEdEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Save Everyday EPG(B)", command=self.save_epg_ed_b)
        self.submitEdEpg.grid(row=3, column=0, pady=(10, 0), columnspan=2)
        self.submitStEpg = customtkinter.CTkButton(self.epg_tab_frame, text="Save Sunday Ticket EPG(B)", command=self.save_epg_st_b)
        self.submitStEpg.grid(row=3, column=2, pady=(10, 0), columnspan=2)

        # TuneAll tabview and corresponding textboxes
        self.epg_tab_frame = self.tabview.add('TuneAll')
        self.epg_tab_frame.columnconfigure(1, weight=1)
        self.epg_tab_frame.columnconfigure(2, weight=1)
        self.epg_tab_frame.rowconfigure(1, weight=1)
        label_3 = customtkinter.CTkLabel(self.epg_tab_frame, text="Everyday TuneAll", font=("Arial", 12))
        label_3.grid(row=0, column=0, pady=(20, 0), columnspan=2)
        self.textbox_3 = customtkinter.CTkTextbox(self.epg_tab_frame)
        self.textbox_3.grid(row=1, column=1, padx=(20, 10), pady=(20, 0), sticky="nsew")

        label_4 = customtkinter.CTkLabel(self.epg_tab_frame, text="Sunday Ticket TuneAll", font=("Arial", 12))
        label_4.grid(row=0, column=2, pady=(20, 0), columnspan=2)
        self.textbox_4 = customtkinter.CTkTextbox(self.epg_tab_frame)
        self.textbox_4.grid(row=1, column=2, padx=(10, 20), pady=(20, 0), sticky="nsew")
        
        #Open .txt file to input to textfields
        self.openEverydayTuneAll = customtkinter.CTkButton(self.epg_tab_frame, text="Open TXT File", command=self.upload_ED_TuneAll)
        self.openEverydayTuneAll.grid(row=2, column=0, pady=(10, 0), columnspan=2)
        self.openSundayTicketTuneAll = customtkinter.CTkButton(self.epg_tab_frame, text="Open TXT File", command=self.upload_ST_TuneAll)
        self.openSundayTicketTuneAll.grid(row=2, column=2, pady=(10, 0), columnspan=2)

        #Submit textfields
        self.submitEdTuneAll = customtkinter.CTkButton(self.epg_tab_frame, text="Save Everyday TuneAll", command=self.save_TuneAll_ed)
        self.submitEdTuneAll.grid(row=3, column=0, pady=(10, 0), columnspan=2)
        self.submitStTuneAll = customtkinter.CTkButton(self.epg_tab_frame, text="Save Sunday Ticket TuneAll", command=self.save_TuneAll_st)
        self.submitStTuneAll.grid(row=3, column=2, pady=(10, 0), columnspan=2)
        

        # set default values
        self.scaling_optionemenu.set("100%")
        self.textbox_1.insert("0.0", "Paste your COM Card (A) EPG used everyday here, or upload it via *.txt file.")
        self.textbox_2.insert("0.0", "Paste your COM Card (A) Sunday Tickey EPG here, or upload it via *.txt file..")
        self.textbox_5.insert("0.0", "Paste your COM Card (B) EPG used everyday here, or upload it via *.txt file.")
        self.textbox_6.insert("0.0", "Paste your COM Card (B) Sunday Tickey EPG here, or upload it via *.txt file..")
        self.textbox_3.insert("0.0", "Paste your standard TuneAll here, or upload it via *.txt file..")
        self.textbox_4.insert("0.0", "Paste your Sunday Tickey TuneAll here, or upload it via *.txt file..")
        self.sidebar_entry.insert('0', '192.168.3.18')
        self.sidebar_switch.configure(state='Off')

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


    def submit_epg_button(self):
        if self.button_trigger == False:
            self.button_trigger = True
        self.submit_epg()
        if self.test_ip_b():
            self.submit_epg_b()


    def submit_tuneall_button(self):
        if self.button_trigger == False:
            self.button_trigger = True
        self.submit_tuneall()


    def submit_both_button(self):
        if self.button_trigger == False:
            self.button_trigger = True
        self.submit_epg()
        self.submit_tuneall()
        if self.test_ip_b():
            self.submit_epg_b()


    def submit_epg(self):
        # Disable the submit button while the automation is in progress
        self.sidebar_button_0.configure(state="disabled")
        self.sidebar_button_1.configure(state="disabled")
        self.start_automation_epg()


    def submit_epg_b(self):
        # Disable the submit button while the automation is in progress
        self.sidebar_button_0.configure(state="disabled")
        self.sidebar_button_1.configure(state="disabled")
        self.start_automation_epg_b()


    def submit_tuneall(self):
        # Disable the submit button while the automation is in progress
        self.sidebar_button_0.configure(state="disabled")
        self.sidebar_button_2.configure(state="disabled")
        self.start_automation_tuneall()


    def submit_both(self):
        self.submit_epg()
        self.submit_tuneall()
        if self.test_ip_b():
            self.submit_epg_b()


    def start_automation_epg(self):
        # Check if the automation thread is already running

        if self.automation_thread_epg is None or not self.automation_thread_epg.is_alive():
            # Start automation in a separate thread
            self.automation_thread_epg = threading.Thread(target=self.automation_worker_epg)
            self.automation_thread_epg.start()
        else:
            self.logmessage('EPG(A) Automation thread is already running')


    def start_automation_epg_b(self):
        # Check if the automation thread is already running

        if self.automation_thread_epg is None or not self.automation_thread_epg.is_alive():
            # Start automation in a separate thread
            self.automation_thread_epg = threading.Thread(target=self.automation_worker_epg_b)
            self.automation_thread_epg.start()
        else:
            self.logmessage('EPG(B) Automation thread is already running')


    def start_automation_tuneall(self):
        # Check if the automation thread is already running
        if self.automation_thread_tuneall is None or not self.automation_thread_tuneall.is_alive():
            # Start automation in a separate thread
            self.automation_thread_tuneall = threading.Thread(target=self.automation_worker_tuneall)
            self.automation_thread_tuneall.start()
        else:
            self.logmessage('TuneAll Automation thread is already running')


    def automation_worker_epg(self):  
        try:
            # Define the channels to replace
            if self.button_trigger:
                event_todo = self.selector_optionemenu.get()   
            else:
                if self.event_status == 'Auto Everyday':
                    event_todo = 'Everyday'
                elif self.event_status == 'Auto Sunday Ticket':
                    event_todo = 'Sunday Ticket'
                else:
                    self.logmessage(f'Error: Unknown event submitted to epg(A) worker thread. Button Press status should say None, however it says: {self.button_trigger}')
                
            
            # Validate day selector for where to get the channellist from
            if event_todo == 'Everyday':
                channels = self.textbox_1.get('1.0', 'end-1c')
            elif event_todo == 'Sunday Ticket':
                channels = self.textbox_2.get('1.0', 'end-1c')
            
            com_card_ip = self.sidebar_entry.get()
            textbox_xpath = '/html/body/pre/form[1]/pre/textarea'
            submit_xpath = '/html/body/pre/form[1]/pre/input[1]'

            # Set up Edge options for headless mode
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--headless')     # Run Edge in headless mode (no GUI)
            edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])

            # Initialize the WebDriver with Chrome options
            driver = webdriver.Edge(options=edge_options)

            # Navigate to the website
            driver.get(f'http://{com_card_ip}/cgi-bin/webcmd?screen=EpgDisplay')

            # Wait for the input element to load ont he webpage
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, textbox_xpath)))

            # Find the input element where you want to paste the text
            input_element = driver.find_element(By.XPATH, textbox_xpath)

            # Clear the input before sending a new string
            input_element.clear()

            # Paste text into the input element
            input_element.send_keys(channels)

            # # Find the button element you want to click
            submit_button = driver.find_element(By.XPATH, submit_xpath)

            # # Click the submit button
            submit_button.click()

        finally:
            # Re-enable the submit button after the automation is completed
            self.sidebar_button_0.configure(state="normal")
            self.sidebar_button_1.configure(state="normal")
            driver.quit()
            if self.button_trigger:
                self.button_trigger = False


    def automation_worker_epg_b(self):  
        try:
            # Define the channels to replace
            if self.button_trigger:
                event_todo = self.selector_optionemenu.get()   
            else:
                if self.event_status == 'Auto Everyday':
                    event_todo = 'Everyday'
                elif self.event_status == 'Auto Sunday Ticket':
                    event_todo = 'Sunday Ticket'
                else:
                    self.logmessage(f'Error: Unknown event submitted to epg(B) worker thread. Button Press status should say None, however it says: {self.button_trigger}')
                
            
            # Validate day selector for where to get the channellist from
            if event_todo == 'Everyday':
                channels = self.textbox_5.get('1.0', 'end-1c')
            elif event_todo == 'Sunday Ticket':
                channels = self.textbox_6.get('1.0', 'end-1c')
            
            com_card_ip = self.sidebar_entry_b.get()
            textbox_xpath = '/html/body/pre/form[1]/pre/textarea'
            submit_xpath = '/html/body/pre/form[1]/pre/input[1]'

            # Set up Edge options for headless mode
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--headless')     # Run Edge in headless mode (no GUI)
            edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])

            # Initialize the WebDriver with Chrome options
            driver = webdriver.Edge(options=edge_options)

            # Navigate to the website
            driver.get(f'http://{com_card_ip}/cgi-bin/webcmd?screen=EpgDisplay')

            # Wait for the input element to load ont he webpage
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, textbox_xpath)))

            # Find the input element where you want to paste the text
            input_element = driver.find_element(By.XPATH, textbox_xpath)

            # Clear the input before sending a new string
            input_element.clear()

            # Paste text into the input element
            input_element.send_keys(channels)

            # # Find the button element you want to click
            submit_button = driver.find_element(By.XPATH, submit_xpath)

            # # Click the submit button
            submit_button.click()

        finally:
            # Re-enable the submit button after the automation is completed
            self.sidebar_button_0.configure(state="normal")
            self.sidebar_button_1.configure(state="normal")
            driver.quit()
            if self.button_trigger:
                self.button_trigger = False


    def automation_worker_tuneall(self):  
        try:
            # Define the channels to replace
            if self.button_trigger:
                event_todo = self.selector_optionemenu.get()   
            else:
                if self.event_status == 'Auto Everyday':
                    event_todo = 'Everyday'
                elif self.event_status == 'Auto Sunday Ticket':
                    event_todo = 'Sunday Ticket'
                else:
                    self.logmessage(f'Error: Unknown event submitted to tuneall worker thread. Button Press status should say None, however it says: {self.button_trigger}')
            
            # Validate day selector for where to get the channellist from
            if event_todo == 'Everyday':
                channels = self.textbox_3.get('1.0', 'end-1c')
            elif event_todo == 'Sunday Ticket':
                channels = self.textbox_4.get('1.0', 'end-1c')
            
            com_card_ip = self.sidebar_entry.get()
            textbox_xpath = '/html/body/pre/form/textarea'
            submit_xpath = '/html/body/pre/form/input[2]'

            # Set up Edge options for headless mode
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--headless')     # Run Edge in headless mode (no GUI)
            edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])

            # Initialize the WebDriver with Chrome options
            driver = webdriver.Edge(options=edge_options)

            # Navigate to the website
            driver.get(f'http://{com_card_ip}/cgi-bin/webcmd?screen=TuneAll')

            # Wait for the input element to load ont he webpage
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, textbox_xpath)))

            # Find the input element where you want to paste the text
            input_element = driver.find_element(By.XPATH, textbox_xpath)

            # Clear the input before sending a new string
            input_element.clear()

            # Paste text into the input element
            input_element.send_keys(channels)

            # Find the button element you want to click
            submit_button = driver.find_element(By.XPATH, submit_xpath)

            # Click the submit button
            submit_button.click()

        finally:
            # Re-enable the submit button after the automation is completed
            self.sidebar_button_0.configure(state="normal")
            self.sidebar_button_2.configure(state="normal")
            driver.quit()
            if self.button_trigger:
                self.button_trigger = False

    ## Scheduler for 'auto submit' is located at the bottom.


    def save_epg_ed(self):
        text_boxes = [self.textbox_1, self.textbox_2]
            
        text_file = filedialog.asksaveasfile(initialdir='%USERPROFILE%\Desktop', title="Save Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        
        if text_file:
            text_content = text_boxes[0].get('1.0', 'end-1c')
            text_file.write(text_content)
            text_file.close()


    def save_epg_st(self):
        text_boxes = [self.textbox_1, self.textbox_2]
            
        text_file = filedialog.asksaveasfile(initialdir='%USERPROFILE%\Desktop', title="Save Sunday Ticket EPG", filetypes=(("Text Files", "*.txt"), ))
        
        if text_file:
            text_content = text_boxes[1].get('1.0', 'end-1c')
            text_file.write(text_content)
            text_file.close()


    def save_epg_ed_b(self):
        text_boxes = [self.textbox_5, self.textbox_6]
            
        text_file = filedialog.asksaveasfile(initialdir='%USERPROFILE%\Desktop', title="Save Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        
        if text_file:
            text_content = text_boxes[0].get('1.0', 'end-1c')
            text_file.write(text_content)
            text_file.close()


    def save_epg_st_b(self):
        text_boxes = [self.textbox_6, self.textbox_6]
            
        text_file = filedialog.asksaveasfile(initialdir='%USERPROFILE%\Desktop', title="Save Sunday Ticket EPG", filetypes=(("Text Files", "*.txt"), ))
        
        if text_file:
            text_content = text_boxes[1].get('1.0', 'end-1c')
            text_file.write(text_content)
            text_file.close()


    def save_TuneAll_ed(self):
        text_boxes = [self.textbox_3, self.textbox_4]
            
        text_file = filedialog.asksaveasfile(initialdir='%USERPROFILE%\Desktop', title="Save Everyday TuneAll", filetypes=(("Text Files", "*.txt"), ))
        
        if text_file:
            text_content = text_boxes[0].get('1.0', 'end-1c')
            text_file.write(text_content)
            text_file.close()


    def save_TuneAll_st(self):

        text_boxes = [self.textbox_3, self.textbox_4]
            
        text_file = filedialog.asksaveasfile(initialdir='%USERPROFILE%\Desktop', title="Save Sunday Ticket TuneAll", filetypes=(("Text Files", "*.txt"), ))
        
        if text_file:
            text_content = text_boxes[1].get('1.0', 'end-1c')
            text_file.write(text_content)
            text_file.close()


    def upload_ED_Epg(self):
        text_file = filedialog.askopenfile(initialdir='%USERPROFILE%\Desktop', title="Open Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        if text_file:
            data = text_file.read()
            self.textbox_1.delete('1.0', 'end')
            self.textbox_1.insert(tk.END, data)
            text_file.close()


    def upload_ST_Epg(self):
        text_file = filedialog.askopenfile(initialdir='%USERPROFILE%\Desktop', title="Open Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        if text_file:
            data = text_file.read()
            self.textbox_2.delete('1.0', 'end')
            self.textbox_2.insert(tk.END, data)
            text_file.close()


    def upload_ed_epg_b(self):
        text_file = filedialog.askopenfile(initialdir='%USERPROFILE%\Desktop', title="Open Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        if text_file:
            data = text_file.read()
            self.textbox_5.delete('1.0', 'end')
            self.textbox_5.insert(tk.END, data)
            text_file.close()


    def upload_st_epg_b(self):
        text_file = filedialog.askopenfile(initialdir='%USERPROFILE%\Desktop', title="Open Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        if text_file:
            data = text_file.read()
            self.textbox_6.delete('1.0', 'end')
            self.textbox_6.insert(tk.END, data)
            text_file.close()


    def upload_ED_TuneAll(self):
        text_file = filedialog.askopenfile(initialdir='%USERPROFILE%\Desktop', title="Open Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        if text_file:
            data = text_file.read()
            self.textbox_3.delete('1.0', 'end')
            self.textbox_3.insert(tk.END, data)
            text_file.close()


    def upload_ST_TuneAll(self):
        text_file = filedialog.askopenfile(initialdir='%USERPROFILE%\Desktop', title="Open Everyday EPG", filetypes=(("Text Files", "*.txt"), ))
        if text_file:
            data = text_file.read()
            self.textbox_4.delete('1.0', 'end')
            self.textbox_4.insert(tk.END, data)
            text_file.close()


    def scheduler(self):
        status = self.sidebar_switch.get()
        clock = strftime('%A')

        if status == 'On':
            self.protocol("WM_DELETE_WINDOW", self.donothing)
            if clock == 'Sunday' and self.sunday_runtime:
                self.event_status = 'Auto Sunday Ticket'
                self.submit_both()
                self.sunday_runtime = False
                self.weekday_runtime = True
                self.logmessage('Sunday Schedule executed -- Sunday Ticket EPG & TuneAll submitted.')
            elif clock != 'Sunday' and self.weekday_runtime:
                self.event_status = 'Auto Everyday'
                self.submit_both()
                self.weekday_runtime = False
                self.sunday_runtime = True
                self.logmessage('Weekday Schedule executed -- Weekday EPG & TuneAll submitted.')
        else:
            self.event_status = None
            self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.after(60000, self.scheduler)


    def time(self):
        string = strftime('%A   %I:%M:%S %p')
        self.clock_lbl.configure(text=string)
        self.clock_lbl.after(1000, self.time)


    def donothing(self):
        self.iconify()


    def logmessage(self, message):
        app_logger.info(strftime('%m-%d-%Y -- %H:%M:%S  :  ') + message)


    def test_ip_b(self):
        if app.sidebar_entry_b.get():
            return True # is not empty
        else:
            return False # is empty


if __name__ == "__main__":
    app = App()
    app.mainloop()
