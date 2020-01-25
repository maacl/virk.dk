# Copyright (c) 2017, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributor(s): Heini L. Ovason
#

import json
import requests
from jinja2 import Template


def get_cvr_no(params_dict):
    """Explanation pending
    """

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

            with open("query.js", "r") as filestream:
                template_string = filestream.read()

            template_object = Template(template_string)

            populated_template = template_object.render(
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

            if resp.status_code is 200:

                try:

                    resp_len = len(json.loads(
                        resp.text).get("hits").get("hits")
                        )

                    if resp_len == 1:

                        hits = json.loads(resp.text).get("hits").get("hits")
                        virksomhed = hits[0].get("_source").get("Vrvirksomhed")
                        cvr_no = virksomhed.get("cvrNummer", "")
                        virk_meta = virksomhed.get("virksomhedMetadata")
                        r_navn = virk_meta.get("nyesteNavn").get("navn", "")
                        r_adresse = virk_meta.get("nyesteBeliggenhedsadresse")
                        r_vejnavn = r_adresse.get("vejnavn", "")
                        r_husnr = r_adresse.get("husnummerFra", "")
                        r_postnr = r_adresse.get("postnummer", "")

                        return f"""{cvr_no};
                                   {r_navn};
                                   {r_vejnavn};
                                   {r_husnr};
                                   {r_postnr};
                                   {search_params};
                                   \n""")

                    else:

                        return f"No hit for --> {navn}"

                except AttributeError as ae:

                    return f"AttributeError --> {ae}"

            else: # if resp.status_code ...

                return f"""HTTP Error --> {resp.status_code}\n
                        HTTP Response Body --> {resp.text}"""

        else: # if org_name ....

            return """ERROR: Company name and/or address info
                        missing in input dictionary."""

    else: # if virk_usr and ...

        return """ERROR: Url and/or user credentials
                    are missing in input dictionary."""
