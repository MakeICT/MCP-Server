"""
Adapted from: https://github.com/WildApricot/ApiSamples/blob/master/python/WaApi.py
"""

import logging

import datetime, pytz
import urllib.request
import urllib.response
import urllib.error
import urllib.parse
import json
import base64
from urllib.error import HTTPError

from pprint import pprint


class WaApiClient(object):
    """Wild apricot API client."""
    auth_endpoint = "https://oauth.wildapricot.org/auth/token"
    api_endpoint = "https://api.wildapricot.org"
    _token = None
    client_id = None
    client_secret = None

    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id
        self.client_secret = client_secret

    def authenticate_with_apikey(self, api_key, scope=None):
        """perform authentication by api key and store result for execute_request method

        api_key -- secret api key from account settings
        scope -- optional scope of authentication request. If None full list of API scopes will be used.
        """
        # print("authenticate_with_apikey")
        self.api_endpoint = "https://api.wildapricot.org"
        if(api_key):
            self.client_id = 'APIKEY'
            self.client_secret = api_key

        scope = "auto" if scope is None else scope
        data = {
            "grant_type": "client_credentials",
            "scope": scope,
            "obtain_refresh_token":"true",
        }
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("ContentType", "application/x-www-form-urlencoded")
        request.add_header("Authorization", 'Basic ' + base64.standard_b64encode(('APIKEY:' + self.client_secret).encode()).decode())

        # pprint(request.__dict__)

        response = urllib.request.urlopen(request)
        # pprint(response.read())

        self._token = WaApiClient._parse_response(response)
        self._token['retrieved_at'] = datetime.datetime.now()
        # print(self._token)
        
        self.set_endpoint_to_default_account()

    def authenticate_with_contact_credentials(self, username, password, scope=None):
        """perform authentication by contact credentials and store result for execute_request method

        username -- typically a contact email
        password -- contact password
        scope -- optional scope of authentication request. If None full list of API scopes will be used.
        """
        scope = "auto" if scope is None else scope
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": scope
        }
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        auth_header = base64.standard_b64encode((self.client_id + ':' + self.client_secret).encode()).decode()
        request.add_header("Authorization", 'Basic ' + auth_header)
        # print(request.__dict__)


        response = urllib.request.urlopen(request)
        # print(response.code)
        self._token = WaApiClient._parse_response(response)
        self._token['retrieved_at'] = datetime.datetime.now()
        
        self.set_endpoint_to_default_account()

    def authenticate_contact(self, username, password, scope=None):
        """perform authentication by contact credentials and store result for execute_request method

        username -- typically a contact email
        password -- contact password
        scope -- optional scope of authentication request. If None full list of API scopes will be used.
        """
        scope = "auto" if scope is None else scope
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": scope
        }
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("ContentType", "application/x-www-form-urlencoded")
        auth_header = base64.standard_b64encode((self.client_id + ':' + self.client_secret).encode()).decode()
        request.add_header("Authorization", 'Basic ' + auth_header)

        try:
            response = urllib.request.urlopen(request)
        except HTTPError as err:
            if err.code == 400:
                return False
            else:
                raise


        if response.code == 200:
            return True
        else:
            return False

        # self._token = WaApiClient._parse_response(response)
        # self._token['retrieved_at'] = datetime.datetime.now()
        
        # self.set_endpoint_to_default_account()

    def set_endpoint_to_default_account(self):
        accounts = self.execute_request("/v2.1/Accounts")
        self.api_endpoint += '/v2.1/Accounts/' + str(accounts[0]['Id']) + '/'

    def execute_request(self, api_url, api_request_object=None, method=None):
        """
        perform api request and return result as an instance of ApiObject or list of ApiObjects

        api_url -- absolute or relative api resource url
        api_request_object -- any json serializable object to send to API
        method -- HTTP method of api request. Default: GET if api_request_object is None else POST
        """
        # print("execute_request")
        if self._token is None:
            raise Exception("Access token is not abtained. "
                               "Call authenticate_with_apikey or authenticate_with_contact_credentials first.")

        if not api_url.startswith("http"):
            api_url = self.api_endpoint + api_url

        if '?' not in api_url:
            api_url += '/'

        if method is None:
            if api_request_object is None:
                method = "GET"
            else:
                method = "POST"

        print("API URL:",api_url)


        request = urllib.request.Request(api_url, method=method)
        if api_request_object is not None:
            request.data = json.dumps(api_request_object).encode()


        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header("Authorization", "Bearer " + self._get_access_token())

        try:
            response = urllib.request.urlopen(request)
            return WaApiClient._parse_response(response)
        except urllib.error.HTTPError as httpErr:
            if httpErr.code == 400:
                raise Exception(httpErr.read())
            else:
                raise

    def _get_access_token(self):
        # print("_get_access_token")
        expires_at = self._token['retrieved_at'] + datetime.timedelta(seconds=self._token['expires_in'] - 100)
        # print("token expires at:", expires_at)
        if datetime.datetime.now() > expires_at:
            self.authenticate_with_apikey(None)
            # self._refresh_auth_token()
        # print(self._token)
        # print(self._token['refresh_token'][14:])
        return self._token['access_token']

    def _refresh_auth_token(self):
        # print("_refresh_auth_token")
        data = {
            "grant_type": "refresh_token",
        }
        if self._token['refresh_token'] is not None:
            data["refresh_token"] = self._token['refresh_token']

        data["scope"] = "auto"
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        auth_header = base64.standard_b64encode((self.client_id + ':' + self.client_secret).encode()).decode()
        request.add_header("Authorization", 'Basic ' + auth_header)
        # request.add_header("Postman-Token", "43ab3ad9-f359-4483-af5b-02e3b0e8cfdc")
        request.add_header("Cache-Control", "no-cache")
        # pprint(request.__dict__)


        response = urllib.request.urlopen(request)

        # pprint(response.__dict__)

        self._token = WaApiClient._parse_response(response)
        self._token['retrieved_at'] = datetime.datetime.now()

    @staticmethod
    def _parse_response(http_response):
        # print("_parse_response")
        response = http_response.read().decode()
        #print ("response: ", response)
        decoded = json.loads(response)
        # pprint(decoded)
        if isinstance(decoded, dict) and len(decoded.keys()) == 1:
            return decoded[list(decoded.keys())[0]]
        else:
            return decoded



    def ConnectAPI(self, API_key=None, username=None, password=None):
        # print("ConnectAPI")
        try:
            if API_key:
                self.authenticate_with_apikey(API_key)
            else:
                self.authenticate_with_contact_credentials(username, password)
            return True
        except urllib.error.HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
        except urllib.error.URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        return False

    def _make_api_request(self, request_string, api_request_object=None, method=None):
        # print("_make_api_request")
        try:    
            return self.execute_request(request_string, api_request_object, method)
        except urllib.error.HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
        except urllib.error.URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        return False

    def _make_rpc_request(self, request_string, rpc_request_object=None):
        try:    
            return self.execute_request(request_string, api_request_object, 'POST')
        except urllib.error.HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
        except urllib.error.URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        return False

    def WADateToDateTime(self, wa_date):
        fixed_date = wa_date[0:22]+wa_date[23:]
        try:
            py_date = datetime.datetime.strptime(fixed_date, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            py_date = datetime.datetime.strptime(fixed_date, '%Y-%m-%dT%H:%M:%S')
        return py_date

    def DateTimeToWADate(self, py_date):
        if not py_date.tzinfo==None:
            utc = pytz.timezone("UTC")
            py_date = py_date.astimezone(utc)
        return py_date.strftime('%Y-%m-%dT%H:%M:%S')


##############################
# Remote Procedure Calls
##############################
    def ApproveMembershipApplication(self, user_id):
        return self._make_rpc_request('')

##############################
# Contacts
##############################
    def GetMe(self):
        return self._make_api_request('/Contacts/me')

    def GetAllContactIDs(self):
        return self._make_api_request('/Contacts/?$async=false&idsOnly')

    def GetAllContacts(self):
        return self._make_api_request('/Contacts?$async=false')

    def GetFilteredContacts(self, filter):
        return self._make_api_request('Contacts?$async=false&$filter=%s' % (filter))

    def GetMemberGroups(self):
        return self._make_api_request('/MemberGroups')

    def GetContactById(self, contact_id): 
        contact = self._make_api_request('/Contacts/%d'%contact_id)
        return contact  

    def GetContactByEmail(self, contact_email): 
        contact = self._make_api_request('/Contacts/?$async=false&$filter=email+eq+' + contact_email)
        return contact

    def GetContactByNameAndDOB(self, contact_first_name, contact_last_name, contact_DOB):
        contact_DOB = self.DateTimeToWADate(contact_DOB)
        contact = self._make_api_request("/Contacts/?$async=false&$filter=firstname+eq+%s+AND+lastname+eq+%s+AND+DOB+eq+'%s'" % (contact_first_name, contact_last_name, contact_DOB))

    def GetContactByName(self, contact_first_name, contact_last_name):
        contact = self._make_api_request("/Contacts/?$async=false&$filter='First+name'+eq+'%s'" % (contact_first_name))

    def GetContactByDOB(self, contact_DOB):
        contact_DOB = self.DateTimeToWADate(contact_DOB)
        contact = self._make_api_request("/Contacts/?$async=false&$filter=DOB+le+'%s'" % (contact_DOB))

    def UpdateContact(self, contact_id, data):
        return self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/Contacts/%d' %(contact_id), data, method="PUT")

    def GetContactField(self, contact_id, field_name):
        contact = self.GetContactById(contact_id)
        field_value = [field["Value"] for field in contact['FieldValues'] if field['FieldName'] == field_name][0]
        return field_value

    def UpdateContactField(self, contact_id, field_name, value):
        data = {
            "Id" : contact_id,
            "FieldValues" : [{
                "FieldName" : field_name,
                "Value" : value
                }]
            }
        return self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/Contacts/%d'%contact_id, data, method="PUT");

    def SetContactMembership(self, contact_id, level_id):
        contact = self.GetContactById(contact_id)
        contact['MembershipEnabled'] = True
        contact['MembershipLevel'] = {'Id':level_id}
        contact['Status'] = "Active"
        # for field in contact['FieldValues']:
        #   if field["SystemCode"]=="Status":
        #       field["Value"]["Id"] = 1
        #       print("\nsetting membership active\n")
        #print(contact)
        return self.UpdateContact(contact_id, contact)

    def SetMemberGroups(self, contact_id, group_ids):
        data = self._make_api_request('/Contacts/%d'%contact_id)
        for field in data["FieldValues"]:
            if field["SystemCode"] == "Groups":
                for group_id in group_ids:
                    field["Value"].append({'Id': group_id})
        return self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/Contacts/%d' %(contact_id), data, method="PUT")

    def SetArchived(self, contact_id):
        pass

    def GetContactFields(self):
        self._make_api_request('ContactFields')



##############################
# Events API Calls
##############################
    def GetEventByID(self, event_id):
        event = self._make_api_request('Events/'+str(event_id))
        return event

    def GetFilteredEvents(self, filter):
        url = 'Events?$filter=' + filter
        events = self._make_api_request(url)
        return events

    def GetEventsByDate(self, start_date, end_date=None):
        if not end_date:
            filter_string = "?$filter=StartDate+eq+" + start_date
        else:
            filter_string = "?$filter=StartDate+gt+"+ start_date + "+AND+StartDate+lt+"+end_date
        events = self._make_api_request("Events/"+filter_string)
        return events

    def DeleteEvent(self, event_id):
        return self._make_api_request('Events/'+str(event_id), method='DELETE')

    def GetRegistrationTypesByEventID(self, event_id):
        reg_types = self._make_api_request('Events/'+str(event_id))
        return reg_types

    def GetUpcomingEvents(self, include_details=False):
        url = 'Events?$filter=IsUpcoming+eq+true%20AND%20RegistrationEnabled+eq+true'
        if include_details:
            url += '&includeEventDetails=true'
        events = self._make_api_request(url)
        return events

    def GetPastEvents(self):
        return self.GetFilteredEvents('IsUpcoming+eq+false')

    def SetEventAccessControl(self, event_id, restricted=False, any_level=True, any_group=True, group_ids=[], level_ids=[]):
        event = self.GetEventByID(event_id)
        if restricted:
            event["AccessLevel"] = "Restricted"
            event["Details"]["AccessControl"]["AccessLevel"] = "Restricted"
            event["Details"]["AccessControl"]["AvailableForAnyLevel"] = any_level
            event["Details"]["AccessControl"]["AvailableForAnyGroup"] = any_group
            groups=[]
            for group_id in group_ids:
                groups.append({'Id':group_id})
            event["Details"]["AccessControl"]["AvailableForGroups"] = groups
            levels=[]
            for levels_id in level_ids:
                levels.append({'Id':level_id})
            event["Details"]["AccessControl"]["AvailableForLevels"] = levels
        else:
            event["AccessLevel"] = ""
            event["Details"]["AccessControl"]["AccessLevel"] = ""
            event["Details"]["AccessControl"]["AvailableForAnyLevel"] = True
            event["Details"]["AccessControl"]["AvailableForAnyGroup"] = True
            event["Details"]["AccessControl"]["AvailableForGroups"] = []
            event["Details"]["AccessControl"]["AvailableForLevels"] = []
        return self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/Events/%d' %(event_id), event, method="PUT")
    
##############################
# Event Registrations
##############################:
    def GetRegistrationByID(self, registration_id):
        registration = self._make_api_request('EventRegistrations?$filter=ID+in+['+str(registration_id)+']')
        return registration


    def GetRegistrantsByEventID(self, event_id, checked_in=None):
        registrants = self._make_api_request('EventRegistrations?eventID='+str(event_id))
        if checked_in==True:
            registrants = [registrant for registrant in registrants if registrant['IsCheckedIn']]
        elif checked_in==False:
            registrants = [registrant for registrant in registrants if not registrant['IsCheckedIn']]

        return registrants

    def GetRegistrationByContactID(self, contact_id):
        registrations = self._make_api_request('EventRegistrations?contactId='+str(contact_id))
        return registrations

    def CheckPendingPayment(self, registration):
        for field in registration["RegistrationFields"]:
            if field["FieldName"] == "StorageBinNumber":
                if field["Value"] == "PendingPayment":
                    return True
        return False

    def MarkPendingPayment(self, registration_id, registration):
        for field in registration["RegistrationFields"]:
            if field["FieldName"] == "StorageBinNumber":
                field["Value"] = "PendingPayment"

        return self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/EventRegistrations/%d' %(registration_id), registration, method="PUT")

    def DeleteRegistration(self, registration_id):
        try:
            response = self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/EventRegistrations/%d' %(registration_id), method="DELETE")
            if response == False:
                return False
        except ValueError:
            pass

    def GetRegistrationsByContact(self, contact_id): 
        registrations = self._make_api_request('/EventRegistrations?contactId=%d'%contact_id)
        return registrations

##############################
# Invoices
##############################
    def GetInvoiceByID(self, invoice_id):
        invoice = self._make_api_request('Invoices/%s' % (invoice_id))
        return invoice

    def GetInvoicesByDate(self, start_date, end_date):
        filter_string = "?StartDate="+ start_date + "&EndDate="+end_date+"&Void=True"
        invoices = self._make_api_request("Invoices"+filter_string)
        return invoices

    def CreateInvoice(self, contact_id, items, creator_id=None, created_date=None):
        if created_date == None:
            created_date = self.DateTimeToWADate(datetime.datetime.now())
        data =  {
                    "OrderDetails": [],  
                    "Contact": {"Id": contact_id},
                    "CreatedDate": created_date,
                    "CreatedBy": {"Id": creator_id},
                }
        
        data["OrderDetails"].append(items)
        print(data)
        invoice = self._make_api_request("Invoices", data, method="POST")
        return invoice

    def FormatInvoiceItem(self, value, notes, taxes=None):
        item =  {
                  "Value": value,
                  "Taxes": taxes,   
                  "Notes": notes,
                }
        return item

##############################
# Payments
##############################
    def CreatePayment(self, contact_id, amount, tender, invoice_id=None, comment=None):
        if isinstance(tender, str):
            tender_id = self.GetTenderByName(tender)['Id']
        elif isinstance(tender, int):
            tender_id = tender
        if not comment:
            comment = "API Generated Payment"
        data = {
            "Value":amount,
            "Contact":{"Id":contact_id},
            "Tender":{"Id":tender_id},
            "Comment":comment,
        }
        if invoice_id:
            data["invoices"] = [{"Id":invoice_id}]
        self._make_api_request('Payments/', data, method="POST")

##############################
# Tenders
##############################
    def GetTenders(self):
        tenders = self._make_api_request("Tenders")
        return tenders

    def GetTenderByName(self, name):
        tenders = self.GetTenders()
        for tender in tenders:
            if tender["Name"] == name:
                return tender
        return None


##############################
# Logs
##############################
    def GetLogItems(self):
        log = self._make_api_request("AuditLogItems/?StartDate=2017-12-05&EndDate=2017-12-07")
        return log

##############################
# MakeICT Specific
##############################
    def SetAuthorizations(self, contact_id, auth_list, date_list):
        auth_map = {'Woodshop':416232,
                    'Metalshop':416231,
                    'Forge':420386,
                    'LaserCutter':416230,
                    'Mig welding':420387, 
                    'Tig welding':420388, 
                    'Stick welding':420389, 
                    'Manual mill':420390,           
                    'Plasma':420391, 
                    'Metal lathes':420392, 
                    'CNC Plasma':420393, 
                    'Intro Tormach':420394, 
                    'Full Tormach':420395}

        auth_text = ''
        auth_group_list = []

        assert len(auth_list) == len(date_list), "List lengths don't match!"

        for index, auth in enumerate(auth_list):
            try:
                auth_group_list.append(auth_map[auth])
                auth_text += auth + '\t' + date_list[index] + '\n'
                #print(auth_group_list)
            except:
                raise
        self.SetMemberGroups(contact_id, auth_group_list)
        auths = self.GetAuthorizations(contact_id)
        auths = auths.strip()
        if auths != '':
            auth_text = '\n' + auth_text
        auths += auth_text
        self.UpdateContactField(contact_id, 'authorizations', auths)

    def GetAuthorizations(self, contact_id):
        #user = self.GetContactById(contact_id)
        auths = self.GetContactField(contact_id, "authorizations")
        return auths