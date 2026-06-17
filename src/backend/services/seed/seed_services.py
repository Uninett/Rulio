
from backend.services.create import get_or_create_service
from backend.utils.logger import set_up_logger
from constants import GLOBAL_TENNANT_ID


logger = set_up_logger(__name__)
class MockRequest:
    session = {"current_tenant_id": GLOBAL_TENNANT_ID}


def seed_services():
    mock_request = MockRequest()

    default_services = [
        # ---------------------------------------------------------------------
        # IP Protocol Objects
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="ICMP_RFC792",
            description="Internet Control Message Protocol for IPv4 diagnostic and error reporting messages, as defined by RFC792.",
            protocol="icmp",
        ),
        get_or_create_service(
            request=mock_request,
            name="ICMPv6_RFC4443",
            description="Internet Control Message Protocol for IPv6 diagnostic and error reporting messages, as defined by RFC4443.",
            protocol="icmpv6",
        ),
        get_or_create_service(
            request=mock_request,
            name="GRE_RFC2784",
            description="Generic Routing Encapsulation used for tunneling packets across IP networks, as defined by RFC2784.",
            protocol="gre",
        ),
        get_or_create_service(
            request=mock_request,
            name="ESP_RFC4303",
            description="Encapsulating Security Payload used by IPsec to provide confidentiality, integrity, and authentication, as defined by RFC4303.",
            protocol="esp",
        ),
        get_or_create_service(
            request=mock_request,
            name="AH_RFC4302",
            description="Authentication Header used by IPsec to provide packet integrity and authentication, as defined by RFC4302.",
            protocol="ah",
        ),
        get_or_create_service(
            request=mock_request,
            name="IP_RFC791",
            description="Internet Protocol service object that matches any IP protocol, based on IPv4 as defined by RFC791.",
            protocol="ip",
        ),

        # ---------------------------------------------------------------------
        # Web Services
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="HTTP_TCP_RFC2616_RFC9110",
            description="Hypertext Transfer Protocol over TCP, as defined by RFC2616 and updated by RFC9110.",
            protocol="tcp",
            port_start=80,
            port_end=80,
        ),
        get_or_create_service(
            request=mock_request,
            name="HTTPS_TCP_RFC2818_RFC9110",
            description="Hypertext Transfer Protocol Secure over TCP using TLS for encrypted web traffic, as defined by RFC2818 and updated by RFC9110.",
            protocol="tcp",
            port_start=443,
            port_end=443,
        ),
        get_or_create_service(
            request=mock_request,
            name="HTTP_Alternate_TCP",
            description="Alternate HTTP service commonly used for web proxies and alternate web applications.",
            protocol="tcp",
            port_start=8080,
            port_end=8080,
        ),
        get_or_create_service(
            request=mock_request,
            name="HTTPS_Alternate_TCP",
            description="Alternate HTTPS service commonly used for secure web applications and management interfaces.",
            protocol="tcp",
            port_start=8443,
            port_end=8443,
        ),

        # ---------------------------------------------------------------------
        # Name Resolution
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="DNS_UDP_RFC1034_RFC1035",
            description="Domain Name System over UDP, as defined by RFC1034 and RFC1035.",
            protocol="udp",
            port_start=53,
            port_end=53,
        ),
        get_or_create_service(
            request=mock_request,
            name="DNS_TCP_RFC1034_RFC1035",
            description="Domain Name System over TCP, as defined by RFC1034 and RFC1035.",
            protocol="tcp",
            port_start=53,
            port_end=53,
        ),
        get_or_create_service(
            request=mock_request,
            name="MDNS_UDP_RFC6762",
            description="Multicast DNS used for local network name resolution, as defined by RFC6762.",
            protocol="udp",
            port_start=5353,
            port_end=5353,
        ),

        # ---------------------------------------------------------------------
        # Remote Access and Management
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="SSH_TCP_RFC4251",
            description="Secure Shell for encrypted remote login and command execution, as defined by RFC4251.",
            protocol="tcp",
            port_start=22,
            port_end=22,
        ),
        get_or_create_service(
            request=mock_request,
            name="Telnet_TCP_RFC854",
            description="Telnet for unencrypted remote terminal access, as defined by RFC854.",
            protocol="tcp",
            port_start=23,
            port_end=23,
        ),
        get_or_create_service(
            request=mock_request,
            name="RDP_TCP",
            description="Remote Desktop Protocol for graphical remote access to systems.",
            protocol="tcp",
            port_start=3389,
            port_end=3389,
        ),
        get_or_create_service(
            request=mock_request,
            name="WinRM_HTTP_TCP",
            description="Windows Remote Management over HTTP for remote administration.",
            protocol="tcp",
            port_start=5985,
            port_end=5985,
        ),
        get_or_create_service(
            request=mock_request,
            name="WinRM_HTTPS_TCP",
            description="Windows Remote Management over HTTPS for encrypted remote administration.",
            protocol="tcp",
            port_start=5986,
            port_end=5986,
        ),

        # ---------------------------------------------------------------------
        # File Transfer
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="FTP_Control_TCP_RFC959",
            description="File Transfer Protocol control channel, as defined by RFC959.",
            protocol="tcp",
            port_start=21,
            port_end=21,
        ),
        get_or_create_service(
            request=mock_request,
            name="FTP_Data_TCP_RFC959",
            description="File Transfer Protocol data channel, as defined by RFC959.",
            protocol="tcp",
            port_start=20,
            port_end=20,
        ),
        get_or_create_service(
            request=mock_request,
            name="SFTP_TCP",
            description="SSH File Transfer Protocol transported over SSH, commonly used for secure file transfer.",
            protocol="tcp",
            port_start=22,
            port_end=22,
        ),
        get_or_create_service(
            request=mock_request,
            name="TFTP_UDP_RFC1350",
            description="Trivial File Transfer Protocol, as defined by RFC1350.",
            protocol="udp",
            port_start=69,
            port_end=69,
        ),

        # ---------------------------------------------------------------------
        # Email Services
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="SMTP_TCP_RFC5321",
            description="Simple Mail Transfer Protocol for email transport, as defined by RFC5321.",
            protocol="tcp",
            port_start=25,
            port_end=25,
        ),
        get_or_create_service(
            request=mock_request,
            name="SMTP_Submission_TCP_RFC6409",
            description="Mail submission service for client message submission, as defined by RFC6409.",
            protocol="tcp",
            port_start=587,
            port_end=587,
        ),
        get_or_create_service(
            request=mock_request,
            name="SMTPS_TCP",
            description="Implicit TLS mail submission service for secure email transport.",
            protocol="tcp",
            port_start=465,
            port_end=465,
        ),
        get_or_create_service(
            request=mock_request,
            name="POP3_TCP_RFC1939",
            description="Post Office Protocol version 3 for email retrieval, as defined by RFC1939.",
            protocol="tcp",
            port_start=110,
            port_end=110,
        ),
        get_or_create_service(
            request=mock_request,
            name="POP3S_TCP",
            description="Secure Post Office Protocol version 3 for encrypted email retrieval.",
            protocol="tcp",
            port_start=995,
            port_end=995,
        ),
        get_or_create_service(
            request=mock_request,
            name="IMAP_TCP_RFC3501",
            description="Internet Message Access Protocol for email retrieval and mailbox access, as defined by RFC3501.",
            protocol="tcp",
            port_start=143,
            port_end=143,
        ),
        get_or_create_service(
            request=mock_request,
            name="IMAPS_TCP",
            description="Secure Internet Message Access Protocol for encrypted mailbox access.",
            protocol="tcp",
            port_start=993,
            port_end=993,
        ),

        # ---------------------------------------------------------------------
        # Directory and Authentication
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="LDAP_TCP_RFC4511",
            description="Lightweight Directory Access Protocol, as defined by RFC4511.",
            protocol="tcp",
            port_start=389,
            port_end=389,
        ),
        get_or_create_service(
            request=mock_request,
            name="LDAPS_TCP",
            description="Lightweight Directory Access Protocol over TLS for secure directory access.",
            protocol="tcp",
            port_start=636,
            port_end=636,
        ),
        get_or_create_service(
            request=mock_request,
            name="Kerberos_TCP_RFC4120",
            description="Kerberos authentication service over TCP, as defined by RFC4120.",
            protocol="tcp",
            port_start=88,
            port_end=88,
        ),
        get_or_create_service(
            request=mock_request,
            name="Kerberos_UDP_RFC4120",
            description="Kerberos authentication service over UDP, as defined by RFC4120.",
            protocol="udp",
            port_start=88,
            port_end=88,
        ),
        get_or_create_service(
            request=mock_request,
            name="RADIUS_Auth_UDP_RFC2865",
            description="Remote Authentication Dial-In User Service for authentication, as defined by RFC2865.",
            protocol="udp",
            port_start=1812,
            port_end=1812,
        ),
        get_or_create_service(
            request=mock_request,
            name="RADIUS_Acct_UDP_RFC2866",
            description="Remote Authentication Dial-In User Service for accounting, as defined by RFC2866.",
            protocol="udp",
            port_start=1813,
            port_end=1813,
        ),

        # ---------------------------------------------------------------------
        # Network Infrastructure
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="DHCP_Server_UDP_RFC2131",
            description="Dynamic Host Configuration Protocol server service, as defined by RFC2131.",
            protocol="udp",
            port_start=67,
            port_end=67,
        ),
        get_or_create_service(
            request=mock_request,
            name="DHCP_Client_UDP_RFC2131",
            description="Dynamic Host Configuration Protocol client service, as defined by RFC2131.",
            protocol="udp",
            port_start=68,
            port_end=68,
        ),
        get_or_create_service(
            request=mock_request,
            name="NTP_UDP_RFC5905",
            description="Network Time Protocol for time synchronization, as defined by RFC5905.",
            protocol="udp",
            port_start=123,
            port_end=123,
        ),
        get_or_create_service(
            request=mock_request,
            name="SNMP_UDP_RFC3411",
            description="Simple Network Management Protocol for device monitoring and management, as defined by RFC3411.",
            protocol="udp",
            port_start=161,
            port_end=161,
        ),
        get_or_create_service(
            request=mock_request,
            name="SNMP_Trap_UDP_RFC3411",
            description="Simple Network Management Protocol trap service for asynchronous event notifications, as defined by RFC3411.",
            protocol="udp",
            port_start=162,
            port_end=162,
        ),
        get_or_create_service(
            request=mock_request,
            name="Syslog_UDP_RFC5424",
            description="Syslog service for log message transport, as defined by RFC5424.",
            protocol="udp",
            port_start=514,
            port_end=514,
        ),
        get_or_create_service(
            request=mock_request,
            name="Syslog_TCP_RFC6587",
            description="Syslog over TCP for reliable log message transport, as defined by RFC6587.",
            protocol="tcp",
            port_start=514,
            port_end=514,
        ),

        # ---------------------------------------------------------------------
        # File Sharing and Directory Services
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="SMB_TCP",
            description="Server Message Block for file and printer sharing in Microsoft networks.",
            protocol="tcp",
            port_start=445,
            port_end=445,
        ),
        get_or_create_service(
            request=mock_request,
            name="NetBIOS_NS_UDP",
            description="NetBIOS Name Service used for name registration and resolution in legacy Microsoft networks.",
            protocol="udp",
            port_start=137,
            port_end=137,
        ),
        get_or_create_service(
            request=mock_request,
            name="NetBIOS_DGM_UDP",
            description="NetBIOS Datagram Service used for connectionless communication in legacy Microsoft networks.",
            protocol="udp",
            port_start=138,
            port_end=138,
        ),
        get_or_create_service(
            request=mock_request,
            name="NetBIOS_SSN_TCP",
            description="NetBIOS Session Service used for session-based communication in legacy Microsoft networks.",
            protocol="tcp",
            port_start=139,
            port_end=139,
        ),
        get_or_create_service(
            request=mock_request,
            name="NFS_TCP_RFC7530",
            description="Network File System for remote file access, as defined by RFC7530.",
            protocol="tcp",
            port_start=2049,
            port_end=2049,
        ),
        get_or_create_service(
            request=mock_request,
            name="NFS_UDP",
            description="Network File System over UDP for remote file access, historically used in some deployments.",
            protocol="udp",
            port_start=2049,
            port_end=2049,
        ),

        # ---------------------------------------------------------------------
        # Databases
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="MySQL_TCP",
            description="MySQL database service for client-server database communication.",
            protocol="tcp",
            port_start=3306,
            port_end=3306,
        ),
        get_or_create_service(
            request=mock_request,
            name="PostgreSQL_TCP",
            description="PostgreSQL database service for client-server database communication.",
            protocol="tcp",
            port_start=5432,
            port_end=5432,
        ),
        get_or_create_service(
            request=mock_request,
            name="MSSQL_TCP",
            description="Microsoft SQL Server database service for client-server database communication.",
            protocol="tcp",
            port_start=1433,
            port_end=1433,
        ),

        # ---------------------------------------------------------------------
        # VPN and Secure Tunneling
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="IKE_UDP_RFC7296",
            description="Internet Key Exchange used for negotiating IPsec security associations, as defined by RFC7296.",
            protocol="udp",
            port_start=500,
            port_end=500,
        ),
        get_or_create_service(
            request=mock_request,
            name="IPsec_NAT_T_UDP_RFC3948",
            description="IPsec NAT Traversal service used to carry IPsec traffic through NAT devices, as defined by RFC3948.",
            protocol="udp",
            port_start=4500,
            port_end=4500,
        ),
        get_or_create_service(
            request=mock_request,
            name="L2TP_UDP_RFC2661",
            description="Layer Two Tunneling Protocol used for VPN tunneling, as defined by RFC2661.",
            protocol="udp",
            port_start=1701,
            port_end=1701,
        ),
        get_or_create_service(
            request=mock_request,
            name="OpenVPN_TCP",
            description="OpenVPN service over TCP for secure remote connectivity.",
            protocol="tcp",
            port_start=1194,
            port_end=1194,
        ),
        get_or_create_service(
            request=mock_request,
            name="OpenVPN_UDP",
            description="OpenVPN service over UDP for secure remote connectivity.",
            protocol="udp",
            port_start=1194,
            port_end=1194,
        ),
        get_or_create_service(
            request=mock_request,
            name="WireGuard_UDP",
            description="WireGuard VPN service for secure modern tunneling.",
            protocol="udp",
            port_start=51820,
            port_end=51820,
        ),

        # ---------------------------------------------------------------------
        # Voice and Real-Time Communication
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="SIP_TCP_RFC3261",
            description="Session Initiation Protocol over TCP for signaling in voice and multimedia sessions, as defined by RFC3261.",
            protocol="tcp",
            port_start=5060,
            port_end=5060,
        ),
        get_or_create_service(
            request=mock_request,
            name="SIP_UDP_RFC3261",
            description="Session Initiation Protocol over UDP for signaling in voice and multimedia sessions, as defined by RFC3261.",
            protocol="udp",
            port_start=5060,
            port_end=5060,
        ),
        get_or_create_service(
            request=mock_request,
            name="SIPS_TCP_RFC3261",
            description="Secure Session Initiation Protocol over TLS for encrypted signaling, as defined by RFC3261.",
            protocol="tcp",
            port_start=5061,
            port_end=5061,
        ),

        # ---------------------------------------------------------------------
        # Monitoring and Observability
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="Prometheus_TCP",
            description="Prometheus metrics service commonly used for monitoring and observability.",
            protocol="tcp",
            port_start=9090,
            port_end=9090,
        ),
        get_or_create_service(
            request=mock_request,
            name="Grafana_TCP",
            description="Grafana web service commonly used for dashboards and observability.",
            protocol="tcp",
            port_start=3000,
            port_end=3000,
        ),

        # ---------------------------------------------------------------------
        # Catch-All Service Objects
        # ---------------------------------------------------------------------
        get_or_create_service(
            request=mock_request,
            name="Any_TCP",
            description="Matches any TCP port.",
            protocol="tcp",
            port_start=1,
            port_end=65535,
        ),
        get_or_create_service(
            request=mock_request,
            name="Any_UDP",
            description="Matches any UDP port.",
            protocol="udp",
            port_start=1,
            port_end=65535,
        ),
    ]
    created_flags = [service[2] for service in default_services]

    if all(created_flags):
        logger.info("All default services were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default services already existed. Missing services were created.")
    else:
        logger.warning("No default services were created because they already all existed.")
    return len(default_services)