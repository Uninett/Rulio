from backend.services.attribute_objects.create_attribute_objects import get_or_create_service_group
from backend.services.get import get_all_services_from_tenant_by_names
from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def seed_servicegroups(actor, tenant_id: int) -> int:

    required_service_names = [
        "ICMP_RFC792",
        "ICMPv6_RFC4443",
        "GRE_RFC2784",
        "ESP_RFC4303",
        "AH_RFC4302",
        "HTTP_TCP_RFC2616_RFC9110",
        "HTTPS_TCP_RFC2818_RFC9110",
        "HTTP_Alternate_TCP",
        "HTTPS_Alternate_TCP",
        "DNS_UDP_RFC1034_RFC1035",
        "DNS_TCP_RFC1034_RFC1035",
        "MDNS_UDP_RFC6762",
        "SSH_TCP_RFC4251",
        "Telnet_TCP_RFC854",
        "RDP_TCP",
        "WinRM_HTTP_TCP",
        "WinRM_HTTPS_TCP",
        "FTP_Control_TCP_RFC959",
        "FTP_Data_TCP_RFC959",
        "TFTP_UDP_RFC1350",
        "POP3_TCP_RFC1939",
        "IMAP_TCP_RFC3501",
        "LDAP_TCP_RFC4511",
        "LDAPS_TCP",
        "Kerberos_TCP_RFC4120",
        "Kerberos_UDP_RFC4120",
        "RADIUS_Auth_UDP_RFC2865",
        "RADIUS_Acct_UDP_RFC2866",
        "DHCP_Server_UDP_RFC2131",
        "DHCP_Client_UDP_RFC2131",
        "NTP_UDP_RFC5905",
        "SNMP_UDP_RFC3411",
        "SNMP_Trap_UDP_RFC3411",
        "Syslog_UDP_RFC5424",
        "Syslog_TCP_RFC6587",
        "SMB_TCP",
        "NetBIOS_NS_UDP",
        "NetBIOS_DGM_UDP",
        "NetBIOS_SSN_TCP",
        "NFS_TCP_RFC7530",
        "NFS_UDP",
        "MySQL_TCP",
        "PostgreSQL_TCP",
        "MSSQL_TCP",
        "IKE_UDP_RFC7296",
        "IPsec_NAT_T_UDP_RFC3948",
        "L2TP_UDP_RFC2661",
        "OpenVPN_TCP",
        "OpenVPN_UDP",
        "WireGuard_UDP",
        "SIP_TCP_RFC3261",
        "SIP_UDP_RFC3261",
        "SIPS_TCP_RFC3261",
        "Prometheus_TCP",
        "Grafana_TCP",
    ]

    services = get_all_services_from_tenant_by_names(
        actor=actor,
        tenant_id=tenant_id,
        names=required_service_names,
    )
    service_ids_by_name = {service.name: service.id for service in services}

    missing_service_names = [name for name in required_service_names if name not in service_ids_by_name]
    if missing_service_names:
        raise ValueError(
            "Cannot seed service groups because these services are missing: " + ", ".join(missing_service_names)
        )

    default_service_groups = [
        # ---------------------------------------------------------------------
        # ACL - Commonly Allowed Client Infrastructure Services
        # Usually permitted from clients to infrastructure for basic operation.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Common_Infrastructure_Client_Services",
            description="Infrastructure services commonly permitted from clients for basic network operation.",
            members=[
                service_ids_by_name["DNS_UDP_RFC1034_RFC1035"],
                service_ids_by_name["DNS_TCP_RFC1034_RFC1035"],
                service_ids_by_name["DHCP_Server_UDP_RFC2131"],
                service_ids_by_name["DHCP_Client_UDP_RFC2131"],
                service_ids_by_name["NTP_UDP_RFC5905"],
                service_ids_by_name["ICMP_RFC792"],
                service_ids_by_name["ICMPv6_RFC4443"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Commonly Allowed Web Access Services
        # Usually permitted outbound and often inbound to published services.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Common_Web_Access_Services",
            description="Web services commonly permitted outbound and often inbound to published applications.",
            members=[
                service_ids_by_name["HTTP_TCP_RFC2616_RFC9110"],
                service_ids_by_name["HTTPS_TCP_RFC2818_RFC9110"],
                service_ids_by_name["HTTP_Alternate_TCP"],
                service_ids_by_name["HTTPS_Alternate_TCP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Restricted Administrative Access Services
        # Usually allowed only from admin networks, jump hosts, or trusted
        # management systems.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Restricted_Administrative_Access_Services",
            description="Administrative access services usually allowed only from trusted management sources.",
            members=[
                service_ids_by_name["SSH_TCP_RFC4251"],
                service_ids_by_name["RDP_TCP"],
                service_ids_by_name["WinRM_HTTP_TCP"],
                service_ids_by_name["WinRM_HTTPS_TCP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Restricted Internal Identity Services
        # Usually allowed only to directory, authentication, and identity
        # infrastructure.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Restricted_Internal_Identity_Services",
            description="Identity and authentication services usually allowed only to directory and authentication infrastructure.",
            members=[
                service_ids_by_name["LDAP_TCP_RFC4511"],
                service_ids_by_name["LDAPS_TCP"],
                service_ids_by_name["Kerberos_TCP_RFC4120"],
                service_ids_by_name["Kerberos_UDP_RFC4120"],
                service_ids_by_name["RADIUS_Auth_UDP_RFC2865"],
                service_ids_by_name["RADIUS_Acct_UDP_RFC2866"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Restricted Internal File Sharing Services
        # Usually allowed only on internal segments and between approved systems.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Restricted_Internal_File_Sharing_Services",
            description="File sharing services usually allowed only on internal segments and between approved systems.",
            members=[
                service_ids_by_name["SMB_TCP"],
                service_ids_by_name["NFS_TCP_RFC7530"],
                service_ids_by_name["NFS_UDP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Restricted Database Services
        # Usually allowed only between approved applications, database servers,
        # and administrative systems.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Restricted_Database_Services",
            description="Database services usually allowed only between approved applications, database servers, and administrative systems.",
            members=[
                service_ids_by_name["MySQL_TCP"],
                service_ids_by_name["PostgreSQL_TCP"],
                service_ids_by_name["MSSQL_TCP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Restricted Monitoring and Logging Services
        # Usually allowed only to monitoring stacks, collectors, and management
        # systems.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Restricted_Monitoring_And_Logging_Services",
            description="Monitoring and logging services usually allowed only to observability platforms, collectors, and management systems.",
            members=[
                service_ids_by_name["SNMP_UDP_RFC3411"],
                service_ids_by_name["SNMP_Trap_UDP_RFC3411"],
                service_ids_by_name["Syslog_UDP_RFC5424"],
                service_ids_by_name["Syslog_TCP_RFC6587"],
                service_ids_by_name["Prometheus_TCP"],
                service_ids_by_name["Grafana_TCP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Commonly Denied Legacy Insecure Services
        # Often denied by default because they are legacy, plaintext, or broadly
        # unnecessary in modern environments.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Deny_Legacy_Insecure_Services",
            description="Legacy or plaintext services commonly denied by default in modern environments.",
            members=[
                service_ids_by_name["Telnet_TCP_RFC854"],
                service_ids_by_name["FTP_Control_TCP_RFC959"],
                service_ids_by_name["FTP_Data_TCP_RFC959"],
                service_ids_by_name["TFTP_UDP_RFC1350"],
                service_ids_by_name["POP3_TCP_RFC1939"],
                service_ids_by_name["IMAP_TCP_RFC3501"],
                service_ids_by_name["NetBIOS_NS_UDP"],
                service_ids_by_name["NetBIOS_DGM_UDP"],
                service_ids_by_name["NetBIOS_SSN_TCP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Commonly Denied Tunneling and VPN Services
        # Often denied unless explicitly required, because they enable overlay
        # networks or encrypted tunnels outside normal policy paths.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Deny_Tunneling_And_VPN_Services",
            description="Tunneling and VPN services commonly denied unless explicitly required.",
            members=[
                service_ids_by_name["GRE_RFC2784"],
                service_ids_by_name["ESP_RFC4303"],
                service_ids_by_name["AH_RFC4302"],
                service_ids_by_name["IKE_UDP_RFC7296"],
                service_ids_by_name["IPsec_NAT_T_UDP_RFC3948"],
                service_ids_by_name["L2TP_UDP_RFC2661"],
                service_ids_by_name["OpenVPN_TCP"],
                service_ids_by_name["OpenVPN_UDP"],
                service_ids_by_name["WireGuard_UDP"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Commonly Denied Voice and Signaling Services
        # Often denied unless the environment intentionally supports voice or
        # multimedia signaling platforms.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Deny_Voice_And_Signaling_Services",
            description="Voice and multimedia signaling services commonly denied unless intentionally in use.",
            members=[
                service_ids_by_name["SIP_TCP_RFC3261"],
                service_ids_by_name["SIP_UDP_RFC3261"],
                service_ids_by_name["SIPS_TCP_RFC3261"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Commonly Denied Local Link Resolution Services
        # Local-link discovery and multicast resolution traffic often denied
        # across routed or security boundaries.
        # ---------------------------------------------------------------------
        get_or_create_service_group(
            actor=actor,
            tenant_id=tenant_id,
            name="Deny_Local_Link_Resolution_Services",
            description="Local-link discovery and multicast name resolution services commonly denied across routed or security boundaries.",
            members=[
                service_ids_by_name["MDNS_UDP_RFC6762"],
            ],
        ),
    ]

    created_flags = [service_group[2] for service_group in default_service_groups]

    if all(created_flags):
        logger.info("All default service groups were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default service groups already existed. Missing service groups were created.")
    else:
        logger.warning("No default service groups were created because they already all existed.")

    return len(default_service_groups)
