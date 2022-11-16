import time
from re import search
import os
from statics import Directories
from user_managment import ClientHandler
# ACCESS_LOG_DIR = ""



class StrickerWatcher:
    def __init__ (
        self,
        check_period,
        access_dir,
        bannig_on,
    ):
        # how often The Watcher Should Loock after strickers
        self.check_period = check_period
        self.access_dir = access_dir
        self.banning_on = bannig_on
        


    def reading_client_logs (self) ->list:
       
        fd = open(self.access_dir,"r") 
        # for counter in range(100):
        lines: list = fd.read().splitlines()
        fd.close()
        return lines

    def count_ip_per_user(self,emails: list):
        # this The Total Connect
        total_current_conn: int = 0
        total_max_conn:int = 0
        # the main Stricker List List That Contains The Stricker Profiles as Chiled
        stricker_list: list = []

        for email in emails:
            # appendinf $ in the end of the email to tell what phrase to lock after
            # Empty Stricker Profile For Getting Empty in every loop
            stricker_profile: dict = {}
            
            # Here We Calculate The User Max Device Connection
            parsed_client: list = email.split("@")
            client_max_conn = int(parsed_client[0])
            # Here we Calcultate The User Max Client
            total_max_conn += client_max_conn 
            # Here We Read The Client Logs
            lines = self.reading_client_logs()
            client_ip_list:list = []
            for line in lines :
                if isinstance(line,str) :
                    if search(email+"$",line):
                        
                        sub_line: list = line.split(" ")
                        client_ip_list.append(sub_line[2])
                        
            client_unique_ip: set = set(client_ip_list)
            client_unique_ip_count = len(client_unique_ip)
            # Here We Calculate Total Current Connection
            total_current_conn += client_unique_ip_count
            if client_unique_ip_count > client_max_conn :
                stricker_profile = {
                    "email":email,
                    "max_conn": client_max_conn,
                    "current_conn": client_unique_ip_count
                }
                stricker_list.append(stricker_profile)

        connection_status = {
            "current_connection": total_current_conn,
            "max_connection": total_max_conn
        }
       
        return (stricker_list , connection_status)

    
    def stanalone_stricker_watcher(self, emails: list, client_handler: ClientHandler):
   
        while True:
            banned_list:list = []
            os.system("> "+self.access_dir)
            time.sleep(self.check_period)

            striker_list , connection = self.count_ip_per_user(emails)
            curr_conn = connection["current_connection"]
            max_conn = connection["max_connection"]
            print("-----------------------------------STRICKERS--------------------------------------")
            for stricker in striker_list:
                stricker_current_conn = stricker["current_conn"]
                stricker_max_conn = stricker["max_conn"]
                print(f"Stricker : \r\n{stricker}")
                # here we will banned the users if banned_on is True 
                if self.banning_on :
                    if stricker_current_conn > stricker_max_conn+1 :
                        stricker_email = stricker["email"]
                        old_id = client_handler.unvalidate_user(stricker_email)
                        self.create_banned_profile_file(stricker_email,old_id)
                        banned_list.append(stricker_email)

            print("----------------------------------------------------------------------------------")
            if self.banning_on :
                print("------------------------------------BANNED----------------------------------------")
                if len(banned_list) != 0 :
                    for banned in banned_list :
                        print(banned)
                else:
                    print("None")
                print("----------------------------------------------------------------------------------")


                    
                
            print(f"Connection Status : {curr_conn}/{max_conn}")


    def create_banned_profile_file(self, email: str, old_id: str):
        with open(Directories.BANNED_DIR,"a") as fd:
            fd.writelines(f"{email} {old_id}\n")
            fd.close()

    def create_stricker_profile_file(self, stricker_list: list, connection_status :dict):
        curr_conn = connection_status["current_connection"]
        max_conn = connection_status["max_connection"]
        with open(Directories.STRICKER_DIR,"a") as f:
            f.write("------------------STRICKR-------------------\n")
            for stricker in stricker_list :
                f.write(f"{stricker}\n")
            f.write("---------------TOTAL CONNECTION-------------\n")
            f.write(f"Connection Status : {curr_conn}/{max_conn}")



                
            
        



    

            

