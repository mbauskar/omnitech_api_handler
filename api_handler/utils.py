"""
makarand
TODO:   1: xml_to_json
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
            return unicode(o).encode('utf-8')
        if hasattr(o, '__dict__'):
            #For objects with a __dict__, return the encoding of the __dict__
            return o.__dict__
        return simplejson.JSONEncoder.default(self, o)

def xml_to_json(xml, as_dict=True):
    """
        convert xml to json, if as_dict is true then return json as dict
    """
    try:
        if isinstance(xml, unicode):
            xml = objectify.fromstring(xml)
        req = objectJSONEncoder().encode(xml)

        if as_dict:
            return json.loads(req)
        else:
            return req
    except Exception, e:
        frappe.throw("Invalid XML Request")

service_response_mapper = {
    "create_service": "CreateServiceResponse",
    "create_customer": "CreateCustomerResponse",
    "disconnect_service": "DisconnedtServiceResponse",
    "delete_customer": "DeleteCustomerResponse",
    "control_action": "ControlActionResponse"
}

def json_to_xml(_json, as_str=True):
    path = frappe.request.path[1:].split("/",2)
    cmd = ""
    if len(path) == 2:
    	cmd = path[1]
        root = etree.Element(service_response_mapper.get(cmd))
        root.extend([E.X_ERROR_CODE(_json.X_ERROR_CODE),
                    E.X_ERROR_DESC(_json.X_ERROR_DESC)])
        return etree.tostring(root)
    else:
    	frappe.throw(_("Invalid URL"))
