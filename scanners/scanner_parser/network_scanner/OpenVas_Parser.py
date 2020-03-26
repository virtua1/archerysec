# -*- coding: utf-8 -*-
#                    _
#     /\            | |
#    /  \   _ __ ___| |__   ___ _ __ _   _
#   / /\ \ | '__/ __| '_ \ / _ \ '__| | | |
#  / ____ \| | | (__| | | |  __/ |  | |_| |
# /_/    \_\_|  \___|_| |_|\___|_|   \__, |
#                                     __/ |
#                                    |___/
# Copyright (C) 2017 Anand Tiwari
#
# Email:   anandtiwarics@gmail.com
# Twitter: @anandtiwarics
#
# This file is part of ArcherySec Project.

from networkscanners.models import ov_scan_result_db, scan_save_db
import datetime
import uuid
import hashlib

from webscanners.zapscanner.views import email_sch_notify

name = ''
creation_time = ''
modification_time = ''
host = ''
port = ''
threat = ''
severity = ''
description = ''
family = ''
cvss_base = ''
cve = ''
bid = ''
xref = ''
tags = ''
banner = ''
vuln_color = None


def xml_parser(root, project_id, scan_id):
    """
    OpenVAS Scanner report parser.
    :param root:
    :param project_id:
    :param scan_id:
    :return:
    """
    for openvas in root.findall(".//result"):
        for r in openvas:
            if r.tag == "name":
                global name
                if r.text is None:
                    name = "NA"
                else:
                    name = r.text

            if r.tag == "creation_time":
                global creation_time
                if r.text is None:
                    creation_time = "NA"
                else:
                    creation_time = r.text

            if r.tag == "modification_time":
                global modification_time
                if r.text is None:
                    modification_time = "NA"
                else:
                    modification_time = r.text
            if r.tag == "host":
                global host
                if r.text is None:
                    host = "NA"
                else:
                    host = r.text

            if r.tag == "port":
                global port
                if r.text is None:
                    port = "NA"
                else:
                    port = r.text
            if r.tag == "threat":
                global threat
                if r.text is None:
                    threat = "NA"
                else:
                    threat = r.text
            if r.tag == "severity":
                global severity
                if r.text is None:
                    severity = "NA"
                else:
                    severity = r.text
            if r.tag == "description":
                global description
                if r.text is None:
                    description = "NA"
                else:
                    description = r.text

            for rr in r.getchildren():
                if rr.tag == "family":
                    global family
                    if rr.text is None:
                        family = "NA"
                    else:
                        family = rr.text
                if rr.tag == "cvss_base":
                    global cvss_base
                    if rr.text is None:
                        cvss_base = "NA"
                    else:
                        cvss_base = rr.text
                if rr.tag == "cve":
                    global cve
                    if rr.text is None:
                        cve = "NA"
                    else:
                        cve = rr.text
                if rr.tag == "bid":
                    global bid
                    if rr.text is None:
                        bid = "NA"
                    else:
                        bid = rr.text

                if rr.tag == "xref":
                    global xref
                    if rr.text is None:
                        xref = "NA"
                    else:
                        xref = rr.text

                if rr.tag == "tags":
                    global tags
                    if rr.text is None:
                        tags = "NA"
                    else:
                        tags = rr.text
                if rr.tag == "type":
                    global banner
                    if rr.text is None:
                        banner = "NA"
                    else:
                        banner = rr.text

        date_time = datetime.datetime.now()
        vul_id = uuid.uuid4()

        dup_data = name + host + severity + port
        duplicate_hash = hashlib.sha256(dup_data.encode('utf-8')).hexdigest()

        match_dup = ov_scan_result_db.objects.filter(
            vuln_duplicate=duplicate_hash).values('vuln_duplicate').distinct()
        lenth_match = len(match_dup)

        vuln_color = ''
        if threat == 'High':
            vuln_color = 'danger'
        elif threat == 'Medium':
            vuln_color = 'warning'
        elif threat == 'Low':
            vuln_color = 'info'
        elif threat == 'Log':
            vuln_color = 'info'

        if lenth_match == 1:
            duplicate_vuln = 'Yes'
        elif lenth_match == 0:
            duplicate_vuln = 'No'
        else:
            duplicate_vuln = 'None'

        false_p = ov_scan_result_db.objects.filter(
            false_positive_hash=duplicate_hash)
        fp_lenth_match = len(false_p)

        if fp_lenth_match == 1:
            false_positive = 'Yes'
        else:
            false_positive = 'No'

        save_all = ov_scan_result_db(scan_id=scan_id,
                                     vul_id=vul_id,
                                     name=name,
                                     creation_time=creation_time,
                                     modification_time=modification_time,
                                     host=host,
                                     port=port,
                                     threat=threat,
                                     severity=severity,
                                     description=description,
                                     family=family,
                                     cvss_base=cvss_base,
                                     cve=cve,
                                     bid=bid,
                                     xref=xref,
                                     tags=tags,
                                     banner=banner,
                                     date_time=date_time,
                                     false_positive=false_positive,
                                     vuln_status='Open',
                                     dup_hash=duplicate_hash,
                                     vuln_duplicate=duplicate_vuln,
                                     project_id=project_id,
                                     vuln_color=vuln_color
                                     )
        save_all.save()

        openvas_vul = ov_scan_result_db.objects.filter(scan_id=scan_id, false_positive='No')

        total_high = len(openvas_vul.filter(threat="High"))
        total_medium = len(openvas_vul.filter(threat="Medium"))
        total_low = len(openvas_vul.filter(threat="Low"))
        total_duplicate = len(openvas_vul.filter(vuln_duplicate='Yes'))
        total_vul = total_high + total_medium + total_low

        scan_save_db.objects.filter(scan_id=scan_id). \
            update(total_vul=total_vul,
                   high_total=total_high,
                   medium_total=total_medium,
                   low_total=total_low,
                   total_dup=total_duplicate,
                   scan_ip=host,
                   )

    subject = 'Archery Tool Scan Status - OpenVAS Report Uploaded'
    message = 'OpenVAS Scanner has completed the scan ' \
              '  %s <br> Total: %s <br>High: %s <br>' \
              'Medium: %s <br>Low %s' % (scan_id, total_vul, total_high, total_medium, total_low)

    email_sch_notify(subject=subject, message=message)
