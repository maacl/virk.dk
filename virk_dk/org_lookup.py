# Copyright (c) 2017, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributor(s): Heini L. Ovason, Søren Howe Gersager
#

import os
import json
import requests

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("virk_dk"),
    autoescape=select_autoescape()
)

def extract_org_info_from_virksomhed(org_dict):
    virksomhed = org_dict.get("_source").get("Vrvirksomhed")
    cvr_no = virksomhed.get("cvrNummer", "")
    virk_meta = virksomhed.get("virksomhedMetadata")
    hoved_branche = virk_meta.get("nyesteHovedbranche")
    r_branchekode = hoved_branche.get("branchekode")
    r_navn = virk_meta.get("nyesteNavn").get("navn", "")
    r_adresse = virk_meta.get("nyesteBeliggenhedsadresse")
    r_vejnavn = r_adresse.get("vejnavn", "")
    r_husnr = r_adresse.get("husnummerFra", "")
    r_postnr = r_adresse.get("postnummer", "")

    return {
        "cvr_no": cvr_no,
        "navn": r_navn,
        "vejnavn": r_vejnavn,
        "husnr": r_husnr,
        "postnr": r_postnr,
        "branchekode": r_branchekode,
    }


def extract_org_info_from_produktionsenhed(org_dict):
    prod = org_dict.get("_source").get("VrproduktionsEnhed")
    prod_meta = prod.get("produktionsEnhedMetadata")
    cvr_no = prod_meta.get("nyesteCvrNummerRelation", "")
    hoved_branche = prod_meta.get("nyesteHovedbranche")
    r_branchekode = hoved_branche.get("branchekode")
    r_navn = prod_meta.get("nyesteNavn").get("navn", "")
    r_adresse = prod_meta.get("nyesteBeliggenhedsadresse")
    r_vejnavn = r_adresse.get("vejnavn", "")
    r_husnr = r_adresse.get("husnummerFra", "")
    r_postnr = r_adresse.get("postnummer", "")

    return {
        "cvr_no": cvr_no,
        "navn": r_navn,
        "vejnavn": r_vejnavn,
        "husnr": r_husnr,
        "postnr": r_postnr,
        "branchekode": r_branchekode,
    }

def get_cvr_no(params_dict):
    """Explanation pending
    """

    template = env.get_template('get_cvr_no_query.j2')

    virk_usr = params_dict.get("virk_usr", None)
    virk_pwd = params_dict.get("virk_pwd", None)
    virk_url = params_dict.get("virk_url", None)

    # No login, no search.
    if virk_usr and virk_pwd and virk_url:

        org_name = params_dict.get("org_name", None)
        street_name = params_dict.get("street_name", None)
        house_no_from = params_dict.get("house_no_from", None)
        zipcode = params_dict.get("zipcode", None)

        # If logged in then these params are the mininimum requirements.
        if org_name and street_name and house_no_from and zipcode:

            navn = org_name.replace("/", "\\\\/")
            vejnavn = street_name
            # TODO: house letters need to be separate query param!
            hus_nr_fra = house_no_from
            postnr = zipcode

            populated_template = template.render(
                navn=navn,
                vejnavn=vejnavn,
                hus_nr_fra=hus_nr_fra,
                postnr=postnr
            )

            url = virk_url
            usr = virk_usr
            pwd = virk_pwd
            headers = {"Content-type": "application/json; charset=UTF-8"}
            payload = json.loads(populated_template)

            resp = requests.post(
                url,
                auth=(usr, pwd),
                json=payload,
                headers=headers
                )

            if resp.status_code == 200:

                try:

                    resp_len = len(json.loads(
                        resp.text).get("hits").get("hits")
                        )

                    if resp_len == 1:

                        hits = json.loads(resp.text).get("hits").get("hits")
                        org_info = extract_org_info(hits[0])
                        return org_info
                    else:

                        # TODO: log(input, err) - Remove return statement

                        return "No hit for -->{0}".format(navn)

                except AttributeError as ae:

                    # TODO: log(input, err) - Remove return statement

                    return "AttributeError --> {0}".format(ae)

            # if resp.status_code ...
            else:

                # TODO: log(input, err) - Remove return statement

                return "HTTP Error --> {0}\nHTTP Body --> {1}".format(
                    resp.status_code,
                    resp.text
                    )

        # if org_name ....
        else:

            # TODO: log(input, err) - Remove return statement

            return "ERROR: Company name and/or address info" \
                    " missing in input dictionary."

    # if virk_usr and ...
    else:

        # TODO: log(input, err) - Remove return statement

        return "ERROR: Url and/or user credentials" \
                " are missing in input dictionary."


def get_org_info_from_cvr(params_dict):
    """
    Return an org_info dict from a cvr_number.
    """
    template = env.get_template('get_org_info_from_cvr.j2')

    virk_usr = params_dict.get("virk_usr", None)
    virk_pwd = params_dict.get("virk_pwd", None)
    virk_url = params_dict.get("virk_url", None)

    if not virk_usr or not virk_pwd or not virk_url:
        return ("ERROR: Url and/or user credentials"
                " are missing in input dictionary.")

    cvr_number = params_dict.get("cvr_number", None)
    if not cvr_number:
        return ("ERROR: CVR number is missing in input dictionary.")

    populated_template = template.render(
        cvr_number=cvr_number
    )

    resp = requests.post(
        virk_url,
        auth=(virk_usr, virk_pwd),
        json=json.loads(populated_template),
        headers={"Content-type": "application/json; charset=UTF-8"}
    )
    if not resp.status_code == 200:
        print(resp.status_code, resp.text)
        return

    hits = resp.json().get("hits").get("hits")

    orgs = []

    for org in hits:
        org_info = extract_org_info_from_virksomhed(org)
        orgs.append(org_info)
    return orgs


def get_org_info_from_p_number(params_dict):
    """
    Return an org_info dict from a p_number.
    """
    template = env.get_template('get_org_info_from_p_number.j2')

    virk_usr = params_dict.get("virk_usr", None)
    virk_pwd = params_dict.get("virk_pwd", None)
    virk_url = params_dict.get("virk_url", None)

    if not virk_usr or not virk_pwd or not virk_url:
        return ("ERROR: Url and/or user credentials"
                " are missing in input dictionary.")

    p_number = params_dict.get("p_number", None)
    if not p_number:
        return ("ERROR: P number is missing in input dictionary.")

    populated_template = template.render(
        p_number=p_number
    )

    resp = requests.post(
        virk_url,
        auth=(virk_usr, virk_pwd),
        json=json.loads(populated_template),
        headers={"Content-type": "application/json; charset=UTF-8"}
    )
    if not resp.status_code == 200:
        print(resp.status_code, resp.text)
        return

    hits = resp.json().get("hits").get("hits")

    orgs = []

    for org in hits:
        org_info = extract_org_info_from_produktionsenhed(org)
        orgs.append(org_info)
    return orgs