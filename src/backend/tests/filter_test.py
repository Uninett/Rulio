
import pytest

from backend.objects.filters import (
            Filter, Rule, RuleFilter, RuleMatch, VersionControl)

class TestFilters:
    
    def test_import_filters(self):
        # Test that imports work and we can use the classes
        assert Filter is not None
        assert Rule is not None
        assert RuleFilter is not None
        assert RuleMatch is not None
        assert VersionControl is not None
