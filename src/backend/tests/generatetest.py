from backend.services import generate_config
from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


class TestGenerateConfig:
    def test_generate_config(self):
        # This is a placeholder test, we should test the database and api integration
        cisco_example_policy = {
            "filename": "cisco_example_policy",
            "filters": [
                {
                    "header": {
                        "targets": {"cisco": "test-filter"},
                        "comment": "Sample comment",
                    },
                    "terms": [
                        {
                            "name": "deny-to-reserved",
                            "destination-address": "RESERVED",
                            "action": "deny",
                        },
                        {
                            "name": "deny-to-bogons",
                            "destination-address": "BOGON",
                            "action": "deny",
                        },
                        {
                            "name": "allow-web-to-mail",
                            "destination-address": "MAIL_SERVERS",
                            "action": "accept",
                        },
                    ],
                }
            ],
        }

        config = generate_config.generate_config(cisco_example_policy, "cisco")
        correct_output = """$Id:$
        ! $Date:$
        ! $Revision:$
        no ip access-list extended test-filter
        ip access-list extended test-filter
        remark $Id:$


        remark deny-to-reserved
        deny ip any 0.0.0.0 0.255.255.255
        deny ip any 10.0.0.0 0.255.255.255


        remark deny-to-bogons
        deny ip any 192.0.0.0 0.0.0.255
        deny ip any 192.0.2.0 0.0.0.255


        remark allow-web-to-mail
        permit ip any host 200.1.1.4
        permit ip any host 200.1.1.5

        exit"""

        logger.info(f"Generated config:\n{config}")
        logger.info(f"Correct output:\n{correct_output}")

        assert config.strip() == correct_output.strip()
