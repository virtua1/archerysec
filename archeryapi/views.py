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

from webscanners.models import zap_scans_db, zap_scan_results_db, burp_scan_db, burp_scan_result_db, arachni_scan_db, \
    netsparker_scan_db, webinspect_scan_db, acunetix_scan_db
from networkscanners.models import scan_save_db, ov_scan_result_db, nessus_report_db, nessus_scan_db
from projects.models import project_db
from webscanners.serializers import WebScanSerializer, \
    WebScanResultSerializer, \
    UploadScanSerializer, \
    WebScanStatusSerializer, \
    ArachniScanStatusSerializer, \
    BurpScanStatusSerializer, \
    NetsparkerScanStatusSerializer, \
    AcunetixStatusSerializer, \
    WebinspectScanStatusSerializer, \
    DependencycheckStatusSerializer, \
    findbugsStatusSerializer, \
    ZapScanStatusDataSerializers

from rest_framework import status
from webscanners.zapscanner.views import launch_zap_scan
from networkscanners import views
from networkscanners.serializers import NetworkScanSerializer, NetworkScanResultSerializer
from archeryapi.serializers import CreateUser
from rest_framework import generics
import uuid
from projects.serializers import ProjectDataSerializers
from scanners.scanner_plugin.web_scanner import burp_plugin
from itertools import chain
import threading
import datetime
import defusedxml.ElementTree as ET
from scanners.scanner_parser.web_scanner import zap_xml_parser, \
    arachni_xml_parser, \
    netsparker_xml_parser, \
    webinspect_xml_parser, \
    burp_xml_parser, \
    acunetix_xml_parser
from rest_framework.response import Response
from rest_framework.views import APIView
import json
from rest_framework.parsers import MultiPartParser, FormParser
from staticscanners.models import bandit_scan_db, bandit_scan_results_db
from scanners.scanner_parser.staticscanner_parser.bandit_report_parser import bandit_report_json
from django.contrib.auth.models import User
from stronghold.decorators import public
from webscanners.arachniscanner.views import launch_arachni_scan
from scanners.scanner_parser.staticscanner_parser import dependencycheck_report_parser, \
    findbugs_report_parser, clair_json_report_parser, trivy_json_report_parser
from lxml import etree
from staticscanners.models import dependencycheck_scan_db, findbugs_scan_db, clair_scan_db, trivy_scan_db
from tools.models import nikto_result_db
from scanners.scanner_parser.tools.nikto_htm_parser import nikto_html_parser
from scanners.scanner_parser.compliance_parser import inspec_json_parser
from compliance.models import inspec_scan_db, inspec_scan_results_db
from scanners.scanner_parser.network_scanner import Nessus_Parser, OpenVas_Parser


class WebScan(generics.ListCreateAPIView):
    queryset = zap_scans_db.objects.all()
    serializer_class = WebScanSerializer

    def get(self, request, format=None, **kwargs):
        """
            GET List all scans and check status.
        """
        all_scans = zap_scans_db.objects.all()
        serialized_scans = WebScanSerializer(all_scans, many=True)
        return Response(serialized_scans.data)

    def post(self, request, format=None, **kwargs):
        """
        Launch scans using this api
        """
        serializer = WebScanSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = uuid.uuid4()
            scanner = request.data.get('scanner')
            target_url = request.data.get('scan_url', )
            project_id = request.data.get('project_id', )
            rescanid = None
            rescan = 'No'
            user = request.user
            if scanner == 'zap_scan':
                # run_s = launch_zap_scan
                thread = threading.Thread(target=launch_zap_scan, args=(target_url,
                                                                        project_id,
                                                                        rescanid,
                                                                        rescan,
                                                                        scan_id,
                                                                        user))
                thread.daemon = True
                thread.start()

            elif scanner == 'burp_scan':
                user = request.user
                date_time = datetime.datetime.now()
                scan_dump = burp_scan_db(scan_id=scan_id,
                                         project_id=project_id,
                                         url=target_url,
                                         date_time=date_time)
                scan_dump.save()
                try:
                    do_scan = burp_plugin.burp_scans(
                        project_id,
                        target_url,
                        scan_id,
                        user
                    )
                    thread = threading.Thread(
                        target=do_scan.scan_launch,
                    )
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    print(e)
            elif scanner == 'arachni':
                thread = threading.Thread(target=launch_arachni_scan, args=(target_url,
                                                                            project_id,
                                                                            rescanid,
                                                                            rescan,
                                                                            scan_id,
                                                                            user))
                thread.daemon = True
                thread.start()

            if not target_url:
                return Response({"error": "No name passed"})
            return Response({"message": "Scan Launched", "scanid": scan_id})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NetworkScan(generics.ListCreateAPIView):
    """
    Network Scan API call to perform scan.
    """
    queryset = scan_save_db.objects.all()
    serializer_class = NetworkScanSerializer

    def get(self, request, format=None, **kwargs):

        """
        Returns a list of all **Network Scans** in the system.

        """
        all_scans = scan_save_db.objects.all()
        serialized_scans = NetworkScanSerializer(all_scans, many=True)
        return Response(serialized_scans.data)

    def post(self, request, format=None, **kwargs):
        """
           Current user's identity endpoint.

        """
        user = request.user
        serializer = NetworkScanSerializer(data=request.data)
        if serializer.is_valid():
            target_ip = request.data.get('scan_ip', )
            project_id = request.data.get('project_id', )
            profile = None
            # views.openvas_scanner(target_ip, project_id, profile)
            thread = threading.Thread(
                target=views.openvas_scanner,
                args=(target_ip, project_id, profile, user)
            )
            thread.daemon = True
            thread.start()
            # time.sleep(5)
            if not target_ip:
                return Response({"error": "No name passed"})
            return Response({"message": "Scan Started"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Project(generics.CreateAPIView):
    queryset = project_db.objects.all()
    serializer_class = ProjectDataSerializers

    def get(self, request, format=None, **kwargs):

        """
        Returns a list of all **Network Scans** in the system.

        """
        all_scans = project_db.objects.all()
        serialized_scans = ProjectDataSerializers(all_scans, many=True)
        return Response(serialized_scans.data)

    def post(self, request, format=None, **kwargs):
        """
           Current user's identity endpoint.

        """
        _project_name = None
        _project_id = None

        serializer = ProjectDataSerializers(data=request.data)
        if serializer.is_valid():
            project_id = uuid.uuid4()
            project_name = request.data.get("project_name", )
            project_start = request.data.get("project_start", )
            project_end = request.data.get("project_end", )
            project_owner = request.data.get("project_owner", )
            project_disc = request.data.get("project_disc", )

            all_project = project_db.objects.filter(project_name=project_name)

            for project in all_project:
                _project_name = project.project_name
                _project_id = project.project_id

            if _project_name == project_name:
                return Response({"message": "Project already existed", "project_id": _project_id})

            else:
                save_project = project_db(project_name=project_name, project_id=project_id,
                                          project_start=project_start, project_end=project_end,
                                          project_owner=project_owner, project_disc=project_disc, )
                save_project.save()

                if not project_name:
                    return Response({"error": "No name passed"})
                return Response({"message": "Project Created", "project_id": project_id})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebScanResult(generics.ListCreateAPIView):
    queryset = zap_scan_results_db.objects.all()
    serializer_class = WebScanResultSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = WebScanResultSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            zap_scan = zap_scan_results_db.objects.filter(scan_id=scan_id)
            burp_scan = burp_scan_result_db.objects.filter(scan_id=scan_id)
            all_scans = chain(zap_scan, burp_scan)
            serialized_scans = WebScanResultSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class ZapScanStatus(generics.ListCreateAPIView):
    queryset = zap_scans_db.objects.all()
    serializer_class = WebScanStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = WebScanStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_scanid', )
            zap_scan = zap_scans_db.objects.filter(scan_scanid=scan_id)
            all_scans = chain(zap_scan)
            serialized_scans = WebScanStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class ArachniScanStatus(generics.ListCreateAPIView):
    queryset = arachni_scan_db.objects.all()
    serializer_class = ArachniScanStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = ArachniScanStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            arachni_scan = arachni_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(arachni_scan)
            serialized_scans = ArachniScanStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class DependencycheckScanStatus(generics.ListCreateAPIView):
    queryset = dependencycheck_scan_db.objects.all()
    serializer_class = DependencycheckStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = DependencycheckStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            dependencycheck_scan = dependencycheck_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(dependencycheck_scan)
            serialized_scans = DependencycheckStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class FindbugsScanStatus(generics.ListCreateAPIView):
    queryset = findbugs_scan_db.objects.all()
    serializer_class = findbugsStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = findbugsStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            findbugs_scan = findbugs_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(findbugs_scan)
            serialized_scans = findbugsStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class BurpScanStatus(generics.ListCreateAPIView):
    queryset = burp_scan_db.objects.all()
    serializer_class = BurpScanStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = BurpScanStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            burp_scan = burp_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(burp_scan)
            serialized_scans = BurpScanStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class NetsparkerScanStatus(generics.ListCreateAPIView):
    queryset = netsparker_scan_db.objects.all()
    serializer_class = NetsparkerScanStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = NetsparkerScanStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            netsparker_scan = netsparker_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(netsparker_scan)
            serialized_scans = NetsparkerScanStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class WebinspectScanStatus(generics.ListCreateAPIView):
    queryset = webinspect_scan_db.objects.all()
    serializer_class = WebinspectScanStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = WebinspectScanStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            webinspect_scan = webinspect_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(webinspect_scan)
            serialized_scans = WebinspectScanStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class AcunetixScanStatus(generics.ListCreateAPIView):
    queryset = acunetix_scan_db.objects.all()
    serializer_class = AcunetixStatusSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = AcunetixStatusSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            acunetix_scan = acunetix_scan_db.objects.filter(scan_id=scan_id)
            all_scans = chain(acunetix_scan)
            serialized_scans = AcunetixStatusSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


class NetworkScanResult(generics.ListCreateAPIView):
    queryset = ov_scan_result_db.objects.all()
    serializer_class = NetworkScanResultSerializer

    def post(self, request, format=None, **kwargs):
        """
            Post request to get all vulnerability Data.
        """
        serializer = NetworkScanResultSerializer(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get('scan_id', )
            all_scans = ov_scan_result_db.objects.filter(scan_id=scan_id)
            serialized_scans = NetworkScanResultSerializer(all_scans, many=True)
            return Response(serialized_scans.data)


@public
class CreateUsers(generics.CreateAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = CreateUser

    def post(self, request, format=None, **kwargs):
        """
            # Post request to get all vulnerability Data.
        """
        serializer = CreateUser(data=request.data)
        if serializer.is_valid():
            username = request.data.get('username')
            password = request.data.get('password')
            email = request.data.get('email')
            user = User.objects.create_user(username, email, password)
            user.save()

            return Response({"message": "User Created !!!"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateZapStatus(generics.CreateAPIView):
    queryset = zap_scans_db.objects.all()

    def post(self, request, format=None, **kwargs):
        _scan_id = None
        _scan_status = None
        serializer = ZapScanStatusDataSerializers(data=request.data)
        if serializer.is_valid():
            scan_id = request.data.get("scan_id")
            scan_status = request.data.get("scan_status")
            zap_scans_db.objects.filter(scan_scanid=scan_id).update(vul_status=scan_status)
            return Response({"message": "ZAP Scanner status updated %s", "Scan Status": scan_status})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpladScanResult(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):

        project_id = request.data.get("project_id")
        scanner = request.data.get("scanner")
        file = request.data.get("filename")
        scan_url = request.data.get("scan_url")
        scan_id = uuid.uuid4()
        scan_status = "100"
        if scanner == "zap_scan":
            date_time = datetime.datetime.now()
            scan_dump = zap_scans_db(scan_url=scan_url,
                                     scan_scanid=scan_id,
                                     date_time=date_time,
                                     project_id=project_id,
                                     vul_status=scan_status,
                                     rescan='No')
            scan_dump.save()
            root_xml = ET.fromstring(file)
            en_root_xml = ET.tostring(root_xml, encoding='utf8').decode('ascii', 'ignore')
            root_xml_en = ET.fromstring(en_root_xml)

            zap_xml_parser.xml_parser(project_id=project_id,
                                      scan_id=scan_id,
                                      root=root_xml_en, source='parser')
            return Response({"message": "ZAP Scan Data Uploaded",
                             "scanner": scanner,
                             "project_id": project_id,
                             "scan_id": scan_id
                             })
        elif scanner == "burp_scan":
            date_time = datetime.datetime.now()
            scan_dump = burp_scan_db(url=scan_url,
                                     scan_id=scan_id,
                                     date_time=date_time,
                                     project_id=project_id,
                                     scan_status=scan_status)
            scan_dump.save()
            # Burp scan XML parser
            root_xml = ET.fromstring(file)
            en_root_xml = ET.tostring(root_xml, encoding='utf8').decode('ascii', 'ignore')
            root_xml_en = ET.fromstring(en_root_xml)

            burp_xml_parser.burp_scan_data(root_xml_en,
                                           project_id,
                                           scan_id)
            return Response({"message": "Burp Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == "arachni":
            date_time = datetime.datetime.now()
            scan_dump = arachni_scan_db(url=scan_url,
                                        scan_id=scan_id,
                                        date_time=date_time,
                                        project_id=project_id,
                                        scan_status=scan_status)
            scan_dump.save()
            root_xml = ET.fromstring(file)
            arachni_xml_parser.xml_parser(project_id=project_id,
                                          scan_id=scan_id,
                                          root=root_xml)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == "acunetix":
            date_time = datetime.datetime.now()
            scan_dump = acunetix_scan_db(
                url=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            root_xml = ET.fromstring(file)
            en_root_xml = ET.tostring(root_xml, encoding='utf8').decode('ascii', 'ignore')
            root_xml_en = ET.fromstring(en_root_xml)
            acunetix_xml_parser.xml_parser(project_id=project_id,
                                           scan_id=scan_id,
                                           root=root_xml_en)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'netsparker':
            date_time = datetime.datetime.now()
            scan_dump = netsparker_scan_db(
                url=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            root_xml = ET.fromstring(file)
            netsparker_xml_parser.xml_parser(project_id=project_id,
                                             scan_id=scan_id,
                                             root=root_xml)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })
        elif scanner == 'webinspect':
            date_time = datetime.datetime.now()
            scan_dump = webinspect_scan_db(
                url=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            root_xml = ET.fromstring(file)
            webinspect_xml_parser.xml_parser(project_id=project_id,
                                             scan_id=scan_id,
                                             root=root_xml)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'banditscan':
            date_time = datetime.datetime.now()
            scan_dump = bandit_scan_db(
                project_name=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            data = json.loads(file)
            bandit_report_json(data=data,
                               project_id=project_id,
                               scan_id=scan_id)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'dependencycheck':
            date_time = datetime.datetime.now()
            scan_dump = dependencycheck_scan_db(
                project_name=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            xml_dat = bytes(bytearray(file, encoding='utf-8'))
            data = etree.XML(xml_dat)
            dependencycheck_report_parser.xml_parser(project_id=project_id,
                                                     scan_id=scan_id,
                                                     data=data)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })
        elif scanner == 'findbugs':
            date_time = datetime.datetime.now()
            scan_dump = findbugs_scan_db(
                project_name=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            root_xml = ET.fromstring(file)
            findbugs_report_parser.xml_parser(project_id=project_id,
                                              scan_id=scan_id,
                                              root=root_xml)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })
        elif scanner == 'clair':
            date_time = datetime.datetime.now()
            scan_dump = clair_scan_db(
                project_name=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            data = json.loads(file)
            clair_json_report_parser.clair_report_json(project_id=project_id,
                                                       scan_id=scan_id,
                                                       data=data)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'trivy':
            date_time = datetime.datetime.now()
            scan_dump = trivy_scan_db(
                project_name=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            data = json.loads(file)
            trivy_json_report_parser.trivy_report_json(project_id=project_id,
                                                       scan_id=scan_id,
                                                       data=data)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'inspec':
            date_time = datetime.datetime.now()
            scan_dump = inspec_scan_db(
                project_name=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            data = json.loads(file)
            inspec_json_parser.inspec_report_json(project_id=project_id,
                                                  scan_id=scan_id,
                                                  data=data)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'nessus':
            date_time = datetime.datetime.now()
            scan_dump = nessus_scan_db(
                scan_ip=scan_url,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                scan_status=scan_status
            )
            scan_dump.save()
            root_xml = ET.fromstring(file)
            en_root_xml = ET.tostring(root_xml, encoding='utf8').decode('ascii', 'ignore')
            root_xml_en = ET.fromstring(en_root_xml)
            Nessus_Parser.nessus_parser(root=root_xml_en,
                                        scan_id=scan_id,
                                        project_id=project_id,
                                        )
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'openvas':
            date_time = datetime.datetime.now()
            scan_dump = scan_save_db(scan_ip=scan_url,
                                     scan_id=scan_id,
                                     date_time=date_time,
                                     project_id=project_id,
                                     scan_status=scan_status)
            scan_dump.save()
            root_xml = ET.fromstring(file)
            en_root_xml = ET.tostring(root_xml, encoding='utf8').decode('ascii', 'ignore')
            root_xml_en = ET.fromstring(en_root_xml)
            OpenVas_Parser.xml_parser(project_id=project_id,
                                      scan_id=scan_id,
                                      root=root_xml_en)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        elif scanner == 'nikto':
            date_time = datetime.datetime.now()
            scan_dump = nikto_result_db(
                date_time=date_time,
                scan_url=scan_url,
                scan_id=scan_id,
                project_id=project_id,
            )
            scan_dump.save()

            nikto_html_parser(file, project_id, scan_id)
            return Response({"message": "Scan Data Uploaded",
                             "project_id": project_id,
                             "scan_id": scan_id,
                             "scanner": scanner
                             })

        return Response({"message": "Scan Data Uploaded"})
