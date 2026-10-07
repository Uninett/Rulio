from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from Rulio.src.backend.objects.filters.version_control import VersionControl


class TestFilters:
    def test_import_filters(self):
        # Test that imports work and we can use the classes
        assert Filter is not None
        assert Rule is not None
        assert RuleMatch is not None
        assert VersionControl is not None
