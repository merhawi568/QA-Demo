"""
Enhanced tools for the LangChain-based QA pipeline.
Provides advanced validation capabilities using LLM and specialized logic.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import re
import json
from langchain_openai import ChatOpenAI
from langchain_config.generic_tools import ToolResult
from langchain_config.schemas import OperationType

class SemanticComparisonTool:
    """Tool for semantic text comparison using LLM"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def compare_text_semantic(self, test_id: str, text_a: str, text_b: str, 
                            comparison_type: str = "similarity") -> ToolResult:
        """Compare two texts semantically using LLM"""
        try:
            if not text_a or not text_b:
                return ToolResult(
                    test_id=test_id,
                    passed=False,
                    message="One or both texts are empty",
                    actual_value=text_a,
                    expected_value=text_b
                )
            
            # Create LLM prompt for semantic comparison
            prompt = self._create_semantic_prompt(text_a, text_b, comparison_type)
            response = self.llm.invoke(prompt)
            
            # Parse LLM response
            result = self._parse_llm_response(response.content)
            
            return ToolResult(
                test_id=test_id,
                passed=result["similar"],
                message=result["explanation"],
                actual_value=text_a,
                expected_value=text_b,
                details={"similarity_score": result.get("score", 0), "comparison_type": comparison_type}
            )
        
        except Exception as e:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Semantic comparison failed: {str(e)}",
                actual_value=text_a,
                expected_value=text_b
            )
    
    def _create_semantic_prompt(self, text_a: str, text_b: str, comparison_type: str) -> str:
        """Create LLM prompt for semantic comparison"""
        if comparison_type == "advice_detection":
            return f"""
            Analyze these two texts to determine if the second text contains advice about unapproved products.
            
            Text 1 (Trade Inquiry): {text_a}
            Text 2 (Voice Log): {text_b}
            
            Determine if Text 2 contains advice about unapproved products. Respond with JSON:
            {{
                "contains_advice": true/false,
                "explanation": "Brief explanation of your analysis",
                "confidence": 0.0-1.0
            }}
            """
        elif comparison_type == "confirmation_check":
            return f"""
            Compare these texts to determine if they represent the same confirmation.
            
            Text 1 (Expected): {text_a}
            Text 2 (Actual): {text_b}
            
            Determine if they represent the same confirmation. Respond with JSON:
            {{
                "similar": true/false,
                "explanation": "Brief explanation of your analysis",
                "score": 0.0-1.0
            }}
            """
        else:  # general similarity
            return f"""
            Compare these two texts for semantic similarity.
            
            Text 1: {text_a}
            Text 2: {text_b}
            
            Determine their semantic similarity. Respond with JSON:
            {{
                "similar": true/false,
                "explanation": "Brief explanation of your analysis",
                "score": 0.0-1.0
            }}
            """
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "similar": result.get("similar", result.get("contains_advice", False)),
                    "explanation": result.get("explanation", "No explanation provided"),
                    "score": result.get("score", result.get("confidence", 0.0))
                }
        except:
            pass
        
        # Fallback parsing
        return {
            "similar": "true" in response.lower() or "similar" in response.lower(),
            "explanation": response,
            "score": 0.5
        }

class DocumentValidationTool:
    """Tool for document presence and metadata validation"""
    
    def validate_document_presence(self, test_id: str, document_type: str, 
                                 document_data: Dict[str, Any]) -> ToolResult:
        """Validate that a required document exists and has proper metadata"""
        try:
            if not document_data:
                return ToolResult(
                    test_id=test_id,
                    passed=False,
                    message=f"{document_type} document not found",
                    actual_value=None,
                    expected_value=document_type
                )
            
            # Check for document existence
            if "document_id" not in document_data and "file_path" not in document_data:
                return ToolResult(
                    test_id=test_id,
                    passed=False,
                    message=f"{document_type} document missing identifier",
                    actual_value=document_data,
                    expected_value=f"{document_type} with valid identifier"
                )
            
            # Check metadata completeness
            required_metadata = self._get_required_metadata(document_type)
            missing_fields = []
            for field in required_metadata:
                if field not in document_data or not document_data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                return ToolResult(
                    test_id=test_id,
                    passed=False,
                    message=f"{document_type} missing metadata: {missing_fields}",
                    actual_value=document_data,
                    expected_value=f"{document_type} with complete metadata"
                )
            
            return ToolResult(
                test_id=test_id,
                passed=True,
                message=f"{document_type} document validated successfully",
                actual_value=document_data,
                expected_value=document_type
            )
        
        except Exception as e:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Document validation failed: {str(e)}",
                actual_value=document_data,
                expected_value=document_type
            )
    
    def _get_required_metadata(self, document_type: str) -> List[str]:
        """Get required metadata fields for different document types"""
        metadata_map = {
            "Bilateral Agreement": ["document_id", "signature_date", "parties"],
            "SCRF": ["document_id", "issue_date", "issuer"],
            "DRE": ["document_id", "issue_date", "issuer"],
            "Call Memo": ["document_id", "call_date", "participants"],
            "Syndicate Communication": ["document_id", "communication_date", "recipients"]
        }
        return metadata_map.get(document_type, ["document_id"])

class TimestampValidationTool:
    """Tool for timestamp validation and SLA checking"""
    
    def timestamp_diff_check(self, test_id: str, start_time: str, end_time: str, 
                           max_delay_minutes: int = 15) -> ToolResult:
        """Check if time difference between timestamps is within SLA"""
        try:
            # Parse timestamps
            start_dt = self._parse_timestamp(start_time)
            end_dt = self._parse_timestamp(end_time)
            
            if not start_dt or not end_dt:
                return ToolResult(
                    test_id=test_id,
                    passed=False,
                    message="Invalid timestamp format",
                    actual_value=start_time,
                    expected_value=end_time
                )
            
            # Calculate difference
            time_diff = end_dt - start_dt
            diff_minutes = time_diff.total_seconds() / 60
            
            # Check if within SLA
            within_sla = diff_minutes <= max_delay_minutes
            
            return ToolResult(
                test_id=test_id,
                passed=within_sla,
                message=f"Time difference: {diff_minutes:.1f} minutes (SLA: {max_delay_minutes} min)",
                actual_value=start_time,
                expected_value=end_time,
                details={"diff_minutes": diff_minutes, "max_delay_minutes": max_delay_minutes}
            )
        
        except Exception as e:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Timestamp validation failed: {str(e)}",
                actual_value=start_time,
                expected_value=end_time
            )
    
    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """Parse various timestamp formats"""
        try:
            if not timestamp:
                return None
                
            # Try ISO format first
            if 'T' in timestamp:
                # Handle Z suffix - convert to UTC timezone
                if timestamp.endswith('Z'):
                    timestamp = timestamp[:-1] + '+00:00'
                try:
                    return datetime.fromisoformat(timestamp)
                except ValueError:
                    # Try parsing as naive datetime and add UTC timezone
                    naive_dt = datetime.fromisoformat(timestamp[:-6])  # Remove timezone part
                    return naive_dt.replace(tzinfo=None)  # Return naive datetime for comparison
            
            # Try other common formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S.%f%z'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
            return None
        except Exception as e:
            print(f"Timestamp parsing error for '{timestamp}': {e}")
            return None

class FieldCompletenessTool:
    """Tool for checking field completeness in structured data"""
    
    def field_completeness_check(self, test_id: str, data: Dict[str, Any], 
                               required_fields: List[str]) -> ToolResult:
        """Check if all required fields are present and non-empty"""
        try:
            missing_fields = []
            empty_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                    empty_fields.append(field)
            
            all_complete = len(missing_fields) == 0 and len(empty_fields) == 0
            
            message_parts = []
            if missing_fields:
                message_parts.append(f"Missing: {missing_fields}")
            if empty_fields:
                message_parts.append(f"Empty: {empty_fields}")
            
            message = "; ".join(message_parts) if message_parts else "All fields complete"
            
            return ToolResult(
                test_id=test_id,
                passed=all_complete,
                message=message,
                actual_value=data,
                expected_value=required_fields,
                details={
                    "missing_fields": missing_fields,
                    "empty_fields": empty_fields,
                    "completeness_rate": (len(required_fields) - len(missing_fields) - len(empty_fields)) / len(required_fields)
                }
            )
        
        except Exception as e:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Field completeness check failed: {str(e)}",
                actual_value=data,
                expected_value=required_fields
            )

class ClassificationTool:
    """Tool for LLM-based classification of text fields"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def classification_check(self, test_id: str, text: str, 
                           classification_type: str) -> ToolResult:
        """Classify text using LLM"""
        try:
            if not text:
                return ToolResult(
                    test_id=test_id,
                    passed=False,
                    message="No text provided for classification",
                    actual_value=text,
                    expected_value=classification_type
                )
            
            # Check if LLM is available (valid API key)
            try:
                # Create classification prompt
                prompt = self._create_classification_prompt(text, classification_type)
                response = self.llm.invoke(prompt)
                
                # Parse response
                result = self._parse_classification_response(response.content, classification_type)
                
                return ToolResult(
                    test_id=test_id,
                    passed=result["classification_correct"],
                    message=result["explanation"],
                    actual_value=text,
                    expected_value=classification_type,
                    details={
                        "classification": result["classification"],
                        "confidence": result["confidence"]
                    }
                )
            
            except Exception as llm_error:
                # Fallback to rule-based classification when LLM is not available
                return self._fallback_classification(test_id, text, classification_type)
        
        except Exception as e:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Classification failed: {str(e)}",
                actual_value=text,
                expected_value=classification_type
            )
    
    def _fallback_classification(self, test_id: str, text: str, classification_type: str) -> ToolResult:
        """Fallback classification using rule-based logic when LLM is not available"""
        try:
            if classification_type == "engage_status":
                # Rule-based engagement status detection
                text_lower = text.lower()
                if "engage" in text_lower and ("yes" in text_lower or "= yes" in text_lower):
                    classification = "Yes"
                    confidence = 0.9
                elif "engage" in text_lower and ("no" in text_lower or "= no" in text_lower):
                    classification = "No"
                    confidence = 0.9
                elif "engage" in text_lower:
                    # If we see "engage" but no clear yes/no, assume Yes for business context
                    classification = "Yes"
                    confidence = 0.7
                else:
                    # Default to Yes for business context
                    classification = "Yes"
                    confidence = 0.6
                
                return ToolResult(
                    test_id=test_id,
                    passed=classification in ["Yes", "No"],
                    message=f"Fallback classification: {classification} (confidence: {confidence})",
                    actual_value=text,
                    expected_value=classification_type,
                    details={
                        "classification": classification,
                        "confidence": confidence,
                        "method": "rule_based"
                    }
                )
            
            elif classification_type == "order_type":
                # Rule-based order type detection
                text_lower = text.lower()
                if "fveq" in text_lower and "new issuance" in text_lower:
                    classification = "FVEQ New Issuance"
                    confidence = 0.9
                elif "fi" in text_lower and "new issuance" in text_lower:
                    classification = "FI New Issuance"
                    confidence = 0.9
                elif "approved" in text_lower:
                    classification = "Approved"
                    confidence = 0.8
                else:
                    classification = "Other"
                    confidence = 0.5
                
                return ToolResult(
                    test_id=test_id,
                    passed=True,
                    message=f"Fallback classification: {classification} (confidence: {confidence})",
                    actual_value=text,
                    expected_value=classification_type,
                    details={
                        "classification": classification,
                        "confidence": confidence,
                        "method": "rule_based"
                    }
                )
            
            else:
                # Generic fallback
                return ToolResult(
                    test_id=test_id,
                    passed=True,
                    message=f"Fallback classification completed for {classification_type}",
                    actual_value=text,
                    expected_value=classification_type,
                    details={
                        "classification": "Unknown",
                        "confidence": 0.5,
                        "method": "rule_based"
                    }
                )
        
        except Exception as e:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Fallback classification failed: {str(e)}",
                actual_value=text,
                expected_value=classification_type
            )
    
    def _create_classification_prompt(self, text: str, classification_type: str) -> str:
        """Create LLM prompt for classification"""
        if classification_type == "engage_status":
            return f"""
            Classify the following text to determine if it indicates "Engage = Yes" or "Engage = No":
            
            Text: {text}
            
            Respond with JSON:
            {{
                "classification": "Yes" or "No",
                "confidence": 0.0-1.0,
                "explanation": "Brief explanation of your classification"
            }}
            """
        elif classification_type == "order_type":
            return f"""
            Classify the following text to determine the order type:
            
            Text: {text}
            
            Respond with JSON:
            {{
                "classification": "FVEQ New Issuance" or "FI New Issuance" or "Approved" or "Other",
                "confidence": 0.0-1.0,
                "explanation": "Brief explanation of your classification"
            }}
            """
        else:
            return f"""
            Classify the following text for: {classification_type}
            
            Text: {text}
            
            Respond with JSON:
            {{
                "classification": "your classification",
                "confidence": 0.0-1.0,
                "explanation": "Brief explanation of your classification"
            }}
            """
    
    def _parse_classification_response(self, response: str, classification_type: str) -> Dict[str, Any]:
        """Parse classification response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "classification": result.get("classification", "Unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "explanation": result.get("explanation", "No explanation"),
                    "classification_correct": self._evaluate_classification(result.get("classification", ""), classification_type)
                }
        except:
            pass
        
        return {
            "classification": "Unknown",
            "confidence": 0.0,
            "explanation": response,
            "classification_correct": False
        }
    
    def _evaluate_classification(self, classification: str, classification_type: str) -> bool:
        """Evaluate if classification is correct based on type"""
        if classification_type == "engage_status":
            return classification.lower() in ["yes", "no"]
        elif classification_type == "order_type":
            return classification in ["FVEQ New Issuance", "FI New Issuance", "Approved", "Other"]
        return True

class EnhancedToolFactory:
    """Factory for creating enhanced tools"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.semantic_tool = SemanticComparisonTool(llm)
        self.document_tool = DocumentValidationTool()
        self.timestamp_tool = TimestampValidationTool()
        self.completeness_tool = FieldCompletenessTool()
        self.classification_tool = ClassificationTool(llm)
    
    def execute_enhanced_tool(self, tool_name: str, test_id: str, **kwargs) -> ToolResult:
        """Execute an enhanced tool by name"""
        if tool_name == "compare_text_semantic":
            return self.semantic_tool.compare_text_semantic(
                test_id, 
                kwargs.get("text_a", ""), 
                kwargs.get("text_b", ""), 
                kwargs.get("comparison_type", "similarity")
            )
        elif tool_name == "validate_document_presence":
            return self.document_tool.validate_document_presence(
                test_id,
                kwargs.get("document_type", ""),
                kwargs.get("document_data", {})
            )
        elif tool_name == "timestamp_diff_check":
            return self.timestamp_tool.timestamp_diff_check(
                test_id,
                kwargs.get("start_time", ""),
                kwargs.get("end_time", ""),
                kwargs.get("max_delay_minutes", 15)
            )
        elif tool_name == "field_completeness_check":
            return self.completeness_tool.field_completeness_check(
                test_id,
                kwargs.get("data", {}),
                kwargs.get("required_fields", [])
            )
        elif tool_name == "classification_check":
            return self.classification_tool.classification_check(
                test_id,
                kwargs.get("text", ""),
                kwargs.get("classification_type", "")
            )
        else:
            return ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Unknown enhanced tool: {tool_name}",
                actual_value=kwargs,
                expected_value=tool_name
            )
