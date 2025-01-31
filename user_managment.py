import qrcode
import json
import subprocess
import base64
from re import search
from statics import UNVALID_UUID,Directories

class ClientHandler :
    def __init__(
        self,
        xray_conf_dir,
    ):
        self.xray_conf_dir = xray_conf_dir
        self.os_tools = OsTools()
       

    def _read_json_conf(self):
        js = None
        with open(self.xray_conf_dir,"r") as xray_config :
            js = json.load(xray_config)

        xray_config.close()

        return js

    def _read_inbounds(self,js_conf)-> dict :
        # TODO : Here We should choose beatwean Inbounds and check them
        inbounds:dict = js_conf["inbounds"][0]
        return inbounds

    def read_clients(self,inbound)-> list:
        clients: list = inbound["settings"]["clients"]
        return clients

    def read_client_emails(self,clients: list)-> list:
        client_list: list = []
        for client in clients :
            client_list.append(client["email"])
   
        return client_list

    # This Function Returns The List of The Config file Emails
    def get_clients_email_list(self):
        client_list: list = []
        js = self._read_json_conf()
        inbound = self._read_inbounds(js)
        clients = self.read_clients(inbound)
        for client in clients :
            client_list.append(client["email"])
        
        return client_list
        


    def get_client_profile(self,email: str):
        js = self._read_json_conf()
        inbound = self._read_inbounds(js)
        clients = self.read_clients(inbound)

        profile: dict = {}

        for client in clients :
            if client["email"] == email :
                profile = client
                break

        return profile

    def get_client_url(self, email: str, domain: str, vpn_name: str):
        profile = self.get_client_profile(email)

        url: str = "vless://"+profile["id"]+"@"+domain+"?path=%2Fuser"+"&"+"security=none"+"&"+"encryption=none"+"&"+"type=ws"+"#"+vpn_name

        return url

    def get_client_qrcode(self,email: str, url: str):
        profile = self.get_client_profile(email)
        image = qrcode.make(url)
        image_name = profile["email"].split("-")
        if len(image_name) == 1:
            image.save(image_name[0]+".PNG")
        elif len(image_name) == 5:
            image.save(image_name[1]+"-"+image_name[2]+".PNG")


    def generate_uuid(self)-> str:
        temp = subprocess.check_output(['xray', 'uuid'])
        uuid = temp.decode("utf-8").strip()
        return uuid

    def add_profile(self,max_conn: int,ph_numer: str,name: str,start_time: str,duration: int):
        '''
            Important Should Check if The User Already Exist or No 
            Step That Should Be done Here : 
            1 - Making The Email String FORMAT : | max_conn@phone_number-first_name-last_name-start_time_duration |
            2 - Genrating The UUID Using The xray command line 
            3 - making the desired Profile 
            4 - reading the config file 
            5 - appending the profile on it
            6 - recreating the json file 
            7 - closing the file
            8 - systemctl restart the xray service
            9 - getting the status 
            10 - if the problem found redoing the thing and puting the prevoius config file
        '''
        # 1
        max_conn = str(max_conn)
        duration = str(duration)
        full_name = name.split(" ")
        first_name = ""
        last_name = ""
        # 2 
        id = self.generate_uuid()
        if len(full_name) == 1:
            first_name = full_name[0]
            last_name = full_name[1]            
        elif len(full_name) == 2 :
            first_name = full_name[0]
            last_name = full_name[1]
        # 3
        email:str = max_conn+"@"+ph_numer+"-"+first_name+"-"+last_name+"-"+start_time+"-"+duration
        # Here we check if The User ALready Exist or Not
        exsistance = self.get_client_profile(email)
        if exsistance :
            return 0

        profile = {
            "id": id,
            "email": email,
            "level": 1
        }
        # 4 
        js = self._read_json_conf()
        # 5
        js["inbounds"][0]["settings"]["clients"].append(profile)
        # 6
        with open(self.xray_conf_dir,"w") as xray_config :
            json.dump(js,xray_config,indent=4)
        # 7
        xray_config.close()
        return 1

    def apply_changes(self):
        self.os_tools.restart_xray()
        status = self.os_tools.status_xray()
        if status :
            print("Change Applied Succesfully")
        else :
            print("Error With The Config File check => xray config.json file and restart service")
            exit()

    def add_user(self,max_conn: int,ph_numer: str,name: str,start_time: str,duration: int):
        result = self.add_profile(max_conn, ph_numer ,name ,start_time ,duration)
        if result :
            print("INFO : User Added !!")
        else :
            print("User Already Exsist(Override)")

    def modify_user(self,email: str,id: str="",device: int = 0):
        # Checking for User Existance if True Continue
        exsistance = self.get_client_profile(email)
        if not exsistance :
            print("User Doesnt Exist to Be modified Please creat The User First")
            return 0
        # reading The Cnnfig File 
        js = self._read_json_conf()
        # Finding The User in array of users .
        for client in js["inbounds"][0]["settings"]["clients"]:
            if client["email"] == email:
                # Changing device Quantity
                if device != 0:
                    parsed_email = email.split("@")
                    parsed_email[0] = str(device)
                    new_email = parsed_email[0]+"@"+parsed_email[1]
                    client["email"] = new_email
                # changing the id of the user
                if id != "":   
                    client["id"] = id

        with open(self.xray_conf_dir,"w") as xray_config :
            json.dump(js,xray_config,indent=4)

        return exsistance

    def unvalidate_banned_user(self, email: str):
        result = self.modify_user(email,id=UNVALID_UUID) 
        if result == 0:
            exit()
        else:
            print("user banned Unvalidated")
            return result["id"]

               
    # This Function Returnes The old uuid
    def unvalidate_user(self, email: str) :
        result = self.modify_user(email,id=UNVALID_UUID)
        if result == 0:
            exit()
        else:
            # Writtimg The Unvalidated User Into The Unvalidated File
            with open(Directories.UNVALIDATED,"a") as f :
                old_id = result["id"]
                f.write(f"{email} {old_id}\n")

            print("user Unvalidated")
            return result["id"]

    # This Function handles the unvalidated users and valiate them again
    def validate_user(self,email: str):
        '''
            Here We have 2 approach for the Validate user :
            user counld be one of this group :
            1 - unvalidated user 
            2 - banned user
            3 - None of this groups
        '''
        uuid_banned = self._is_client_banned(email)
        uuid_unvalid = self._is_client_unvalidated(email)
        # check for banned person to validate
        if len(uuid_banned) and len(uuid_unvalid) == 0 :
            #TODO we need to check it from config.json too
            self._remove_banned_client_from_file(email)
            self.modify_user(email= email,id= uuid_banned)
            print("Banned Client Validated Succesfully")
        # check for unvalidates person to validate
        if len(uuid_banned) ==0 and len(uuid_unvalid) :
            self._remove_unvalidate_client_from_file(email)
            self.modify_user(email= email,id= uuid_unvalid)
            print("Unvalidated Client Validated Succesfully")

        # here is expection if user not banned or unvalidated is deleted or unvalidated by hand
        if len(uuid_banned) == 0 and len(uuid_unvalid) == 0 :
            print("Desired Client doesnt found in Banned or Unvalidated files")

        
            



        # 1 Opening The banned Users 
        # banne_lines = []
        # unvalidated_lines = []
        # banned_client = False 
        # unvalidated_client = False
        # unvalidated_write_enable = False
        # with open(Directories.BANNED_DIR,"r") as f:
        #     banne_lines = f.read().splitlines()
        #     for line in banne_lines : 
        #         splited_line = line.split(" ")
        #         if splited_line[0] == email:
        #             banned_client = True
        #             unvalidated_client = False
        #             # removing the banned client from the list
        #             banne_lines.remove(line)
        #             # here we Modify the user in config.json
        #             self.modify_user(email=email,id=splited_line[1])
        #             print("user validated again")
        #             self.apply_changes()
        #         else :
        #             banned_client = False
        #             unvalidated_client = True

        # if (banned_client == True) and (unvalidated_client == False) :
        #     # rewriting the file again for commiting  The Changes
        #     with open(Directories.BANNED_DIR,"w") as f :
        #         for line in banne_lines:
        #             f.write(line+"\n") 
        # if (banned_client == False) and (unvalidated_client == True) :
        #     print("IM HEREEEEEEEEEE")
        #     # here we check for unvalidated user not banned one
        #     with open(Directories.UNVALIDATED,"r") as f:
        #         unvalidated_lines = f.read().splitlines()
        #         for line in unvalidated_lines : 
        #             splited_line = line.split(" ")
        #             if splited_line[0] == email:
        #                 print("FINIEEDDDD")
        #                 banned_client = False
        #                 unvalidated_client = True
        #                 unvalidated_write_enable = True
        #                 # removing the unvalidated client from the list
        #                 unvalidated_lines.remove(line)
        #                 self.modify_user(email=email,id=splited_line[1])
        #                 print("user validated again")
        #                 self.apply_changes()

        #     if unvalidated_write_enable :
        #         with open(Directories.UNVALIDATED,"a") as f:
        #             for line in unvalidated_lines:
        #                 f.write(line+"\n") 



    def _is_client_banned(self,email) :
        lines = self._read_banned()
        exsist = ""
        for line in lines : 
            splited_line = line.split(" ")
            if splited_line[0] == email:
                exsist = splited_line[1]
        return exsist

    def _is_client_unvalidated(self,email) :
        lines = self._read_unvalidated()
        exsist = ""
        for line in lines : 
            splited_line = line.split(" ")
            if splited_line[0] == email:
                exsist = splited_line[1]
        return exsist

    def _read_banned(self):
        with open(Directories.BANNED_DIR,"r") as f:
            lines = f.read().splitlines()
        return lines

    def _read_unvalidated(self):
        with open(Directories.UNVALIDATED,"r") as f:
            lines = f.read().splitlines()
        return lines
        

    def _remove_banned_client_from_file(self, email: str) :
        lines: list = self._read_banned()
        # removing client from the file
        for line in lines :
            splited_line = line.split(" ")
            if splited_line[0] == email :
                lines.remove(line)
                break

        with open(Directories.BANNED_DIR,"w") as f:
            for line in lines :
                f.write(line+"\n")

    def _remove_unvalidate_client_from_file(self, email: str) :
        lines: list = self._read_unvalidated()
        # removing client from the file
        for line in lines :
            splited_line = line.split(" ")
            if splited_line[0] == email :
                lines.remove(line)
                break

        with open(Directories.UNVALIDATED,"w") as f:
            for line in lines :
                f.write(line+"\n")

            

 


            




                    






        




class OsTools:
    def __init__(self):
        self.command = "xray"

    def restart_xray(self):
        subprocess.check_output(f"systemctl restart {self.command}", shell=True)
    
    def status_xray(self):
        status = subprocess.check_output(f"systemctl status {self.command}", shell=True)
        str_status = status.decode()
        if str_status.find("Active: active (running)") != -1 :
            return True
        else :
            return False







# class ClientManager:
#     def __init__(
#         self,
#         xray_conf_dir,
#     ):

#         self.xray_conf_dir = xray_conf_dir
#         self.xray_conf_file = None
#         self.xray_conf = None
#         self.clients_json: dict = {}
#         self.client_profile: dict = {}
#         self.client_profiles: list = []

#         self._read_conf()



#     def _read_conf(self):
#         self.xray_conf_file = open(self.xray_conf_dir,"r")
#         self.xray_conf = self.xray_conf_file.read()
#         self.xray_conf_file.close()

#     def _read_clients(self):
#         self.clients_json = json.loads(self.xray_conf)
#         inbounds = self.clients_json["inbounds"][0]
#         settings = inbounds["settings"]
#         self.client_profiles = settings["clients"]

#         return self.client_profiles
  
       
#     def get_client(self, email: str):
#         # Maybe Parsing The name Only???
#         self._read_clients()    
#         target_client: dict = {}
#         for client in self.client_profiles :
#             if client["email"] == email :
#                 target_client = client
#                 break

#         return target_client

#     def get_client_email(self):

#         client_list: list = []

#         self._read_clients()    
#         for client in self.client_profiles:
#            client_list.append(client["email"])

#         return client_list



        

#     def generat_client_url(self, client ,domain: str , vpn_name: str) -> str:

#         client:dict = self.get_client(client)

#         client_uuid = client["id"]
#         client_email = client["email"]

#         client_full_json: dict = {
#             "v": "2",
#             "ps": vpn_name,
#             "add": domain,
#             "port": "80",
#             "id": client_uuid,
#             "aid": "0",
#             "scy": "auto",
#             "net": "ws",
#             "type": "none",
#             "host": "",
#             "path": "/user",
#             "tls": "",
#             "sni": "",
#             "alpn": ""
#         }
#         # Making Base 64 Clients
#         dumped = json.dumps(client_full_json)
#         message_bytes = dumped.encode('ascii')
#         base64_bytes = base64.b64encode(message_bytes)
#         base64_message = base64_bytes.decode('ascii')
#         final_profile = "vmess://"+ base64_message
#         return final_profile,client_email


#     def generate_qr(self, url, client):
#         image = qrcode.make(url)
#         image.save(client+".PNG")

#     def get_clinet_property(self, email) ->dict:
#         prop: dict = self.get_client(email)
#         if len(prop) :

#             full_profile: dict = {}

#             user_uuid = str(prop['id'])
#             #user_email = str(prop['email'])
#             user_email = "2@091245585-parsa-oskouie-1401/5/8-1401/7/8"
#             parsed_email= user_email.split("@")
#             max_connection = parsed_email[0]
#             client_prop_unparsed = parsed_email[1]

#             client_prop_parsed: list = client_prop_unparsed.split("-") 
#             print(len(client_prop_parsed))

#             if len(client_prop_parsed) == 5:
#                 full_profile ={
#                     'Id': user_uuid,
#                     'Num/TId': client_prop_parsed[0],
#                     'Name': client_prop_parsed[1],
#                     'LastName': client_prop_parsed[2],
#                     'Start_Time': client_prop_parsed[3],
#                     'End_Time':client_prop_parsed[4]
#                 }
#             else :
#                 full_profile ={
#                     'Id': user_uuid,
#                     'Num/TId': client_prop_unparsed,
#                     'Name': 'Unknown' ,
#                     'LastName': 'Unknown',
#                     'Start_Time': 'Unknown',
#                     'End_Time': 'Unknown'
#                 }

#             return full_profile            
#         else:
#             print(prop)
#             print("User Not Found")

#     def generate_uuid(self)-> str:
#         temp = subprocess.check_output(['xray', 'uuid'])
#         uuid = temp.decode("utf-8").strip()
#         return uuid


#     def add_user(self, user_identity: str):
#         #self._read_conf()
#         profiles = self._read_clients()
#         #print(self.client_profiles)
#         user_uuid = self.generate_uuid()
#         user_dict = {
#             'id': user_uuid,
#             'email': user_identity,
#             'level': 1,
#             'alterId': 0,
#         }

#         conf = json.loads(self.xray_conf)
#         conf["inbounds"][0]["settings"]["clients"].append(user_dict)
#         json_conf =  json.dumps(conf, 
#                         indent=4,  
#                         separators=(',',': '))
#         print(json_conf)