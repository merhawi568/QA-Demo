"""
Generic test tools for the LangChain-based QA pipeline.
These tools provide configurable operations for different types of validations.
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import re
from langchain_config.schemas import OperationType, TestType

class ToolResult:
    """Standard result format for all tools"""
    def __init__(self, test_id: str, passed: bool, message: str, 
                 actual_value: Any = None, expected_value: Any = None, 
                 details: Dict[str, Any] = None):
        self.test_id = test_id
        self.passed = passed
        self.message = message
        self.actual_value = actual_value
        self.expected_value = expected_value
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "passed": self.passed,
            "message": self.message,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "details": self.details,
            "timestamp": self.timestamp
        }

class CompareTool:
    """Generic comparison tool for various data types"""
    
    @staticmethod
    def execute(test_id: str, data_a: Any, data_b: Any, operation: OperationType, 
                parameters: Dict[str, Any] = None) -> ToolResult:
        """Execute comparison operation"""
        parameters = parameters or {}
        
        try:
            if operation == OperationType.EQUALS:
                passed, message = CompareTool._equals(data_a, data_b, parameters)
            elif operation == OperationType.NOT_EQUALS:
                passed, message = CompareTool._not_equals(data_a, data_b, parameters)
            elif operation == OperationType.GREATER_THAN:
                passed, message = CompareTool._greater_than(data_a, data_b, parameters)
            elif operation == OperationType.LESS_THAN:
                passed, message = CompareTool._less_than(data_a, data_b, parameters)
            elif operation == OperationType.ROUNDED_EQUALITY:
                passed, message = CompareTool._rounded_equality(data_a, data_b, parameters)
            else:
                return ToolResult(test_id, False, f"Unsupported operation: {operation}")
            
            return ToolResult(
                test_id=test_id,
                passed=passed,
                message=message,
                actual_value=data_a,
                expected_value=data_b,
                details={"operation": operation.value, "parameters": parameters}
            )
        
        except Exception as e:
            return ToolResult(test_id, False, f"Comparison failed: {str(e)}")
    
    @staticmethod
    def _equals(data_a: Any, data_b: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if two values are equal"""
        case_sensitive = parameters.get("case_sensitive", True)
        
        if not case_sensitive and isinstance(data_a, str) and isinstance(data_b, str):
            data_a, data_b = data_a.lower(), data_b.lower()
        
        passed = data_a == data_b
        message = f"Values are {'equal' if passed else 'not equal'}: {data_a} vs {data_b}"
        return passed, message
    
    @staticmethod
    def _not_equals(data_a: Any, data_b: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if two values are not equal"""
        passed = data_a != data_b
        message = f"Values are {'not equal' if passed else 'equal'}: {data_a} vs {data_b}"
        return passed, message
    
    @staticmethod
    def _greater_than(data_a: Any, data_b: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if data_a > data_b"""
        try:
            # Convert to numeric if possible
            if isinstance(data_a, str) and isinstance(data_b, str):
                data_a, data_b = float(data_a), float(data_b)
            elif isinstance(data_a, str):
                data_a = float(data_a)
            elif isinstance(data_b, str):
                data_b = float(data_b)
            
            passed = data_a > data_b
            message = f"{data_a} is {'greater than' if passed else 'not greater than'} {data_b}"
            return passed, message
        except (ValueError, TypeError):
            return False, f"Cannot compare non-numeric values: {data_a} vs {data_b}"
    
    @staticmethod
    def _less_than(data_a: Any, data_b: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if data_a < data_b"""
        try:
            # Convert to numeric if possible
            if isinstance(data_a, str) and isinstance(data_b, str):
                data_a, data_b = float(data_a), float(data_b)
            elif isinstance(data_a, str):
                data_a = float(data_a)
            elif isinstance(data_b, str):
                data_b = float(data_b)
            
            passed = data_a < data_b
            message = f"{data_a} is {'less than' if passed else 'not less than'} {data_b}"
            return passed, message
        except (ValueError, TypeError):
            return False, f"Cannot compare non-numeric values: {data_a} vs {data_b}"
    
    @staticmethod
    def _rounded_equality(data_a: Any, data_b: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if two numeric values are equal within specified precision"""
        precision = parameters.get("precision", 2)
        
        try:
            # Convert to Decimal for precise arithmetic
            if isinstance(data_a, str):
                data_a = Decimal(str(data_a))
            else:
                data_a = Decimal(str(data_a))
            
            if isinstance(data_b, str):
                data_b = Decimal(str(data_b))
            else:
                data_b = Decimal(str(data_b))
            
            # Round to specified precision
            rounded_a = data_a.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            rounded_b = data_b.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            passed = rounded_a == rounded_b
            message = f"Values are {'equal' if passed else 'not equal'} at {precision} decimal places: {rounded_a} vs {rounded_b}"
            return passed, message
        except (ValueError, TypeError, Exception):
            return False, f"Cannot perform rounded comparison: {data_a} vs {data_b}"

class DateRangeTool:
    """Tool for date range validations"""
    
    @staticmethod
    def execute(test_id: str, date_value: Any, operation: OperationType,
                parameters: Dict[str, Any] = None) -> ToolResult:
        """Execute date range operation"""
        parameters = parameters or {}
        
        try:
            if operation == OperationType.IN_RANGE:
                passed, message = DateRangeTool._in_range(date_value, parameters)
            elif operation == OperationType.GREATER_THAN:
                passed, message = DateRangeTool._greater_than(date_value, parameters)
            elif operation == OperationType.LESS_THAN:
                passed, message = DateRangeTool._less_than(date_value, parameters)
            else:
                return ToolResult(test_id, False, f"Unsupported date operation: {operation}")
            
            return ToolResult(
                test_id=test_id,
                passed=passed,
                message=message,
                actual_value=date_value,
                details={"operation": operation.value, "parameters": parameters}
            )
        
        except Exception as e:
            return ToolResult(test_id, False, f"Date validation failed: {str(e)}")
    
    @staticmethod
    def _in_range(date_value: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if date is within specified range"""
        min_offset_days = parameters.get("min_offset_days", 0)
        max_offset_days = parameters.get("max_offset_days", 30)
        reference_date = parameters.get("reference_date")
        
        # Parse date value
        if isinstance(date_value, str):
            date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        elif isinstance(date_value, datetime):
            date_obj = date_value
        else:
            return False, f"Cannot parse date: {date_value}"
        
        # Use reference date or current date
        if reference_date:
            if isinstance(reference_date, str):
                ref_date = datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
            else:
                ref_date = reference_date
        else:
            ref_date = datetime.now()
        
        # Calculate range
        min_date = ref_date + timedelta(days=min_offset_days)
        max_date = ref_date + timedelta(days=max_offset_days)
        
        passed = min_date <= date_obj <= max_date
        message = f"Date {date_obj.date()} is {'within' if passed else 'outside'} range [{min_date.date()}, {max_date.date()}]"
        return passed, message
    
    @staticmethod
    def _greater_than(date_value: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if date is greater than reference"""
        reference_date = parameters.get("reference_date")
        if not reference_date:
            return False, "Reference date required for greater_than operation"
        
        # Parse dates
        if isinstance(date_value, str):
            date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        elif isinstance(date_value, datetime):
            date_obj = date_value
        else:
            return False, f"Cannot parse date: {date_value}"
        
        if isinstance(reference_date, str):
            ref_date = datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
        else:
            ref_date = reference_date
        
        passed = date_obj > ref_date
        message = f"Date {date_obj.date()} is {'greater than' if passed else 'not greater than'} {ref_date.date()}"
        return passed, message
    
    @staticmethod
    def _less_than(date_value: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if date is less than reference"""
        reference_date = parameters.get("reference_date")
        if not reference_date:
            return False, "Reference date required for less_than operation"
        
        # Parse dates
        if isinstance(date_value, str):
            date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        elif isinstance(date_value, datetime):
            date_obj = date_value
        else:
            return False, f"Cannot parse date: {date_value}"
        
        if isinstance(reference_date, str):
            ref_date = datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
        else:
            ref_date = reference_date
        
        passed = date_obj < ref_date
        message = f"Date {date_obj.date()} is {'less than' if passed else 'not less than'} {ref_date.date()}"
        return passed, message

class ValidationTool:
    """Tool for presence and format validations"""
    
    @staticmethod
    def execute(test_id: str, data: Any, operation: OperationType,
                parameters: Dict[str, Any] = None) -> ToolResult:
        """Execute validation operation"""
        parameters = parameters or {}
        
        try:
            if operation == OperationType.EXISTS:
                passed, message = ValidationTool._exists(data, parameters)
            elif operation == OperationType.NOT_EXISTS:
                passed, message = ValidationTool._not_exists(data, parameters)
            elif operation == OperationType.CONTAINS:
                passed, message = ValidationTool._contains(data, parameters)
            else:
                return ToolResult(test_id, False, f"Unsupported validation operation: {operation}")
            
            return ToolResult(
                test_id=test_id,
                passed=passed,
                message=message,
                actual_value=data,
                details={"operation": operation.value, "parameters": parameters}
            )
        
        except Exception as e:
            return ToolResult(test_id, False, f"Validation failed: {str(e)}")
    
    @staticmethod
    def _exists(data: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if data exists and is not empty"""
        field_name = parameters.get("field", "data")
        
        if data is None:
            passed = False
            message = f"{field_name} does not exist (None)"
        elif isinstance(data, str) and not data.strip():
            passed = False
            message = f"{field_name} exists but is empty"
        elif isinstance(data, (list, dict)) and len(data) == 0:
            passed = False
            message = f"{field_name} exists but is empty"
        else:
            passed = True
            message = f"{field_name} exists and has value"
        
        return passed, message
    
    @staticmethod
    def _not_exists(data: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if data does not exist or is empty"""
        field_name = parameters.get("field", "data")
        
        if data is None:
            passed = True
            message = f"{field_name} does not exist (None)"
        elif isinstance(data, str) and not data.strip():
            passed = True
            message = f"{field_name} exists but is empty"
        elif isinstance(data, (list, dict)) and len(data) == 0:
            passed = True
            message = f"{field_name} exists but is empty"
        else:
            passed = False
            message = f"{field_name} exists and has value"
        
        return passed, message
    
    @staticmethod
    def _contains(data: Any, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Check if data contains specified value"""
        search_value = parameters.get("search_value")
        field_name = parameters.get("field", "data")
        case_sensitive = parameters.get("case_sensitive", True)
        
        if search_value is None:
            return False, "search_value parameter required for contains operation"
        
        if isinstance(data, str):
            if not case_sensitive:
                data, search_value = data.lower(), str(search_value).lower()
            else:
                search_value = str(search_value)
            passed = search_value in data
        elif isinstance(data, (list, dict)):
            passed = search_value in data
        else:
            passed = str(search_value) in str(data)
        
        message = f"{field_name} {'contains' if passed else 'does not contain'} '{search_value}'"
        return passed, message

class GenericToolFactory:
    """Factory for creating and executing generic tools"""
    
    @staticmethod
    def execute_tool(tool_type: TestType, test_id: str, data: Any, 
                    operation: OperationType, parameters: Dict[str, Any] = None,
                    additional_data: Any = None) -> ToolResult:
        """Execute a tool based on its type"""
        parameters = parameters or {}
        
        if tool_type == TestType.COMPARE:
            if additional_data is None:
                return ToolResult(test_id, False, "Compare tool requires two data values")
            return CompareTool.execute(test_id, data, additional_data, operation, parameters)
        
        elif tool_type == TestType.DATE_RANGE_CHECK:
            return DateRangeTool.execute(test_id, data, operation, parameters)
        
        elif tool_type == TestType.VALIDATE_PRESENCE:
            return ValidationTool.execute(test_id, data, operation, parameters)
        
        elif tool_type == TestType.EQUALITY_CHECK:
            if additional_data is None:
                return ToolResult(test_id, False, "Equality check requires two data values")
            return CompareTool.execute(test_id, data, additional_data, OperationType.EQUALS, parameters)
        
        elif tool_type == TestType.ROUNDED_EQUALITY:
            if additional_data is None:
                return ToolResult(test_id, False, "Rounded equality check requires two data values")
            return CompareTool.execute(test_id, data, additional_data, OperationType.ROUNDED_EQUALITY, parameters)
        
        else:
            return ToolResult(test_id, False, f"Unsupported tool type: {tool_type}")
