"""
Test Template for {ComponentName}

Spec: {path/to/component.spec.md}

This template demonstrates the standard test structure for G5 contract-based testing.
"""

import pytest
from typing import Any, Generator
from unittest.mock import Mock, patch
from pathlib import Path

# Import the component under test
# from src.module import ComponentName, SpecificError


class TestComponentName:
    """
    Tests for ComponentName.
    
    Organized by contract type:
    1. PRE conditions (validation tests)
    2. POST conditions (behavior tests)  
    3. ERROR conditions (error handling tests)
    4. Edge cases
    """
    
    # === Fixtures ===
    
    @pytest.fixture
    def component(self) -> "ComponentName":
        """Create a fresh component instance for each test."""
        return ComponentName()
    
    @pytest.fixture
    def component_with_data(self, component: "ComponentName") -> "ComponentName":
        """Create a component with pre-populated data."""
        component.add("key1", "value1")
        component.add("key2", "value2")
        return component
    
    # === PRE Condition Tests ===
    # Test that preconditions are enforced (invalid inputs raise errors)
    
    def test_method_rejects_none_input(self, component: "ComponentName"):
        """PRE: input must not be None"""
        with pytest.raises(ValueError, match="input cannot be None"):
            component.method(None)
    
    def test_method_rejects_empty_string(self, component: "ComponentName"):
        """PRE: input must not be empty"""
        with pytest.raises(ValueError, match="input cannot be empty"):
            component.method("")
    
    def test_method_rejects_negative_value(self, component: "ComponentName"):
        """PRE: value must be positive"""
        with pytest.raises(ValueError, match="value must be positive"):
            component.method(-1)
    
    # === POST Condition Tests ===
    # Test that postconditions hold after successful execution
    
    def test_method_returns_expected_type(self, component: "ComponentName"):
        """POST: returns correct type"""
        result = component.method(valid_input)
        assert isinstance(result, ExpectedType)
    
    def test_method_returns_expected_value(self, component: "ComponentName"):
        """POST: returns expected value"""
        result = component.method("test_input")
        assert result == "expected_output"
    
    def test_method_modifies_state_correctly(self, component: "ComponentName"):
        """POST: state is modified as expected"""
        original_count = component.count
        component.method("input")
        assert component.count == original_count + 1
    
    # === ERROR Condition Tests ===
    # Test that specific errors are raised in error conditions
    
    def test_method_raises_not_found_error(self, component: "ComponentName"):
        """ERROR: NotFoundError when item doesn't exist"""
        with pytest.raises(NotFoundError) as exc_info:
            component.get("nonexistent")
        assert "nonexistent" in str(exc_info.value)
    
    def test_method_raises_validation_error(self, component: "ComponentName"):
        """ERROR: ValidationError when input invalid"""
        with pytest.raises(ValidationError):
            component.validate(invalid_data)
    
    # === Edge Case Tests ===
    
    def test_method_handles_empty_collection(self, component: "ComponentName"):
        """Edge: behavior with empty collection"""
        result = component.process([])
        assert result == []
    
    def test_method_handles_single_item(self, component: "ComponentName"):
        """Edge: behavior with single item"""
        result = component.process(["only_one"])
        assert len(result) == 1
    
    def test_method_handles_large_input(self, component: "ComponentName"):
        """Edge: behavior with large input"""
        large_input = list(range(10000))
        result = component.process(large_input)
        assert len(result) == 10000
    
    # === Parametrized Tests ===
    
    @pytest.mark.parametrize("input_val,expected", [
        ("a", "A"),
        ("hello", "HELLO"),
        ("", ""),
        ("123", "123"),
    ])
    def test_method_various_inputs(
        self, 
        component: "ComponentName", 
        input_val: str, 
        expected: str
    ):
        """POST: returns correct result for various inputs"""
        assert component.transform(input_val) == expected
    
    @pytest.mark.parametrize("invalid_input", [
        None,
        "",
        -1,
        float("nan"),
    ])
    def test_method_rejects_invalid_inputs(
        self,
        component: "ComponentName",
        invalid_input: Any
    ):
        """PRE: rejects various invalid inputs"""
        with pytest.raises((ValueError, TypeError)):
            component.method(invalid_input)


class TestComponentNameIntegration:
    """Integration tests for ComponentName with dependencies."""
    
    @pytest.fixture
    def mock_dependency(self) -> Mock:
        """Create mock dependency."""
        mock = Mock()
        mock.fetch.return_value = {"data": "test"}
        return mock
    
    def test_component_uses_dependency_correctly(
        self,
        mock_dependency: Mock
    ):
        """Integration: component calls dependency as expected"""
        component = ComponentName(dependency=mock_dependency)
        component.process_data()
        
        mock_dependency.fetch.assert_called_once()
    
    @patch("module.external_service.call")
    def test_component_handles_external_failure(
        self,
        mock_external: Mock
    ):
        """Integration: handles external service failure"""
        mock_external.side_effect = ConnectionError("Service unavailable")
        
        component = ComponentName()
        with pytest.raises(ServiceError):
            component.call_external()
