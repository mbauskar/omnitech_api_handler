"""
makarand
1: xml_to_json
2: json_to_xml
"""

import json
import frappe
import simplejson
from lxml import etree
from lxml import objectify
from lxml.builder import E

class objectJSONEncoder(simplejson.JSONEncoder):
    """A specialized JSON encoder that can handle simple lxml objectify types
       >>> from lxml import objectify
       >>> obj = objectify.fromstring("<Book><price>1.50</price><author>W. Shakespeare</author></Book>")
       >>> objectJSONEncoder().encode(obj)
       '{"price": 1.5, "author": "W. Shakespeare"}'
    """
    def default(self,o):
        if isinstance(o, objectify.IntElement):
            return int(o)
        if isinstance(o, objectify.NumberElement) or isinstance(o, objectify.FloatElement):
            return float(o)
        if isinstance(o, objectify.ObjectifiedDataElement):
            return unicode(o).encode('utf-8').strip()
        if hasattr(o, '__dict__'):
            #For objects with a __dict__, return the encoding of the __dict__
            return o.__dict__
        return simplejson.JSONEncoder.default(self, o)

service_request_mapper = {
    "create_service": "CreateService",
    "create_customer": "CreateCustomer",
    "disconnect_service": "DisconnectService",
    "delete_customer": "DeleteCustomer",
    "control_action": "ControlAction"
}

def xml_to_json(xml, as_dict=True):
    """
        convert xml to json, if as_dict is true then return json as dict
    """
    try:
        if isinstance(xml, unicode):
            xml = objectify.fromstring(xml)
        req = objectJSONEncoder().encode(xml)
        req = json.loads(req)
        print req

        req_root_tag = service_request_mapper.get(frappe.local.form_dict.cmd)
        if req.get(req_root_tag):
            result = type_correction(req.get(req_root_tag))
            if as_dict:
                return req.get(req_root_tag)
            else:
                return json.dumps(req.get(req_root_tag))
        else:
            raise Exception("Invalid XML Request")
    except Exception, e:
        import traceback
        print traceback.format_exc()
        if "Invalid type" in str(e):
            frappe.throw(str(e))
        else:
            frappe.throw("Invalid XML Request")

def type_correction(_dict):
    try:
        for key, val in _dict.iteritems():
            if key == "P_TRXN_NO":
                _dict.update({"P_TRXN_NO":int(val)})
            else:
                _dict.update({key:str(val)})
        return _dict
    except Exception, e:
        raise Exception("Invalid type in request parameters")

service_response_mapper = {
    "create_service": "CreateServiceResponse",
    "create_customer": "CreateCustomerResponse",
    "disconnect_service": "DisconnectServiceResponse",
    "delete_customer": "DeleteCustomerResponse",
    "control_action": "ControlActionResponse"
}

def json_to_xml(_json, as_str=True):
    """
        converts {"X_ERROR_CODE":"01","X_ERROR_DESC":"DESC"} to xml as follows
        xml : <CreateServiceResponse>
                <X_ERROR_CODE>01</X_ERROR_CODE>
                <X_ERROR_DESC>DESC</X_ERROR_DESC>
              </CreateServiceResponse>
    """
    path = frappe.request.path[1:].split("/",2)
    if len(path) == 2:
        cmd = path[1]
        root = etree.Element(service_response_mapper.get(cmd) or "ServiceResponse")
        # root = etree.Element("ServiceResponse")
        root.extend([E.X_ERROR_CODE(_json.X_ERROR_CODE),
                    E.X_ERROR_DESC(_json.X_ERROR_DESC)])
        return etree.tostring(root)
    else:
        raise Exception("Invalid URL")

def send_mail(args, subject, template):
    """send mail to user"""
    from frappe.utils.user import get_user_fullname
    from frappe.utils import get_url
    try:
        args.update({
            'title': "Omnitech ERPNext-Service Update Notification"
        })

        # sender = frappe.session.user not in STANDARD_USERS and frappe.session.user or None
        # sender = "Administrator"
        sender = None

        frappe.sendmail(recipients=args.get("email"), sender=sender, subject=subject,
            message=frappe.get_template(template).render(args))
        return True
    except Exception, e:
        import traceback
        print "notify", traceback.format_exc()
        return False