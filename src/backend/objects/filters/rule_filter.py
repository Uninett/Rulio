

class RuleFilter:
    def __init__(self, rule_id=None, rule_name=None, rule_type=None):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.rule_type = rule_type

    def __str__(self):
        return f"RuleFilter(rule_id={self.rule_id}, rule_name={self.rule_name}, rule_type={self.rule_type})"