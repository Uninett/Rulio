

class RuleMatch:
    def __init__(self, id: int, rule_id: int, match: bool, object_type:str, object_id: int):
        self.id = id
        self.rule_id = rule_id
        self.match = match
        self.object_type = object_type
        self.object_id = object_id

    def __str__(self):
        return f"RuleMatch(id={self.id}, rule_id={self.rule_id}, match={self.match}, object_type='{self.object_type}', object_id={self.object_id})"