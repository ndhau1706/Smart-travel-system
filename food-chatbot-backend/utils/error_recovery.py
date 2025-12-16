"""
Error Recovery and Smart Fallback System.
Progressive degradation + intelligent suggestions.
"""
from typing import List, Dict, Optional, Tuple
import json


class ErrorRecoveryEngine:
    """Handles zero-result queries with intelligent suggestions."""
    
    def __init__(self):
        self.recovery_strategies = [
            self._relax_distance,
            self._relax_budget,
            self._expand_cuisine,
            self._find_alternatives,
            self._suggest_popular,
        ]
    
    def get_recovery_suggestion(
        self,
        original_params: Dict,
        search_results: List,
        original_query: str
    ) -> Dict:
        """
        Generate recovery suggestion when search returns 0 results.
        
        Args:
            original_params: Original search parameters
            search_results: Current search results (empty)
            original_query: User's original query
            
        Returns:
            {
                "status": "recovery_suggested",
                "suggestion": "Không tìm thấy phở rẻ...",
                "action": "relax_distance",
                "new_params": {...},
                "explanation": "...",
            }
        """
        # Try each recovery strategy in order
        for strategy in self.recovery_strategies:
            result = strategy(original_params, original_query)
            if result:
                return result
        
        # Last resort: generic suggestion
        return {
            "status": "no_recovery",
            "suggestion": "Xin lỗi, không tìm thấy quán phù hợp với tiêu chí của bạn.",
            "action": "none",
            "explanation": "Hệ thống không tìm thấy kết quả phù hợp.",
        }
    
    def _relax_distance(self, params: Dict, query: str) -> Optional[Dict]:
        """Try expanding search radius."""
        if params.get('max_distance'):
            original_distance = params['max_distance']
            new_distance = original_distance * 2  # Double the radius
            
            new_params = params.copy()
            new_params['max_distance'] = new_distance
            
            return {
                "status": "recovery_suggested",
                "suggestion": f"Không tìm thấy quán gần trong bán kính {original_distance}km. Nếu mở rộng lên {new_distance}km, sẽ tìm được nhiều quán hơn. Thử xem?",
                "action": "relax_distance",
                "new_params": new_params,
                "explanation": f"Bán kính tìm kiếm được mở rộng từ {original_distance}km → {new_distance}km",
                "confidence": 0.8,
            }
        return None
    
    def _relax_budget(self, params: Dict, query: str) -> Optional[Dict]:
        """Try increasing budget range."""
        if params.get('max_budget'):
            original_budget = params['max_budget']
            new_budget = original_budget + 50000  # Add 50k
            
            new_params = params.copy()
            new_params['max_budget'] = new_budget
            
            return {
                "status": "recovery_suggested",
                "suggestion": f"Không tìm thấy quán dưới {original_budget:,}đ. Nhưng có rất nhiều quán từ {original_budget:,} đến {new_budget:,}đ. Xem thử?",
                "action": "relax_budget",
                "new_params": new_params,
                "explanation": f"Ngân sách được nâng lên từ {original_budget:,}đ → {new_budget:,}đ",
                "confidence": 0.75,
            }
        return None
    
    def _expand_cuisine(self, params: Dict, query: str) -> Optional[Dict]:
        """Try expanding cuisine search."""
        from utils.food_taxonomy import semantic_engine
        
        if params.get('cuisines'):
            original_cuisines = params['cuisines']
            # Get similar cuisines for each original cuisine
            expanded_cuisines = []
            for cuisine in original_cuisines:
                similar = semantic_engine.get_similar_dishes(cuisine)
                expanded_cuisines.extend(similar)
            
            expanded_cuisines = list(set(expanded_cuisines + original_cuisines))
            
            if len(expanded_cuisines) > len(original_cuisines):
                new_params = params.copy()
                new_params['cuisines'] = expanded_cuisines
                
                added_cuisines = [c for c in expanded_cuisines if c not in original_cuisines]
                
                return {
                    "status": "recovery_suggested",
                    "suggestion": f"Không tìm thấy {', '.join(original_cuisines)}. Nhưng có {', '.join(added_cuisines)} tương tự. Xem thử?",
                    "action": "expand_cuisine",
                    "new_params": new_params,
                    "explanation": f"Mở rộng loại món ăn: {', '.join(original_cuisines)} → {', '.join(expanded_cuisines)}",
                    "confidence": 0.7,
                }
        return None
    
    def _find_alternatives(self, params: Dict, query: str) -> Optional[Dict]:
        """Find similar restaurant types based on attributes."""
        # Try finding restaurants with similar attributes but different cuisine
        new_params = params.copy()
        
        # Remove most specific filters
        if new_params.get('cuisines'):
            del new_params['cuisines']
        
        return {
            "status": "recovery_suggested",
            "suggestion": "Không tìm thấy quán phù hợp với yêu cầu cụ thể. Nhưng có quán khác cũng rất tốt. Xem gợi ý?",
            "action": "find_alternatives",
            "new_params": new_params,
            "explanation": "Tìm kiếm quán ăn khác dựa trên các tiêu chí khác",
            "confidence": 0.65,
        }
    
    def _suggest_popular(self, params: Dict, query: str) -> Optional[Dict]:
        """Last resort: suggest most popular restaurants."""
        new_params = {
            "sort_by": "rating",
            "limit": 5,
        }
        
        return {
            "status": "recovery_suggested",
            "suggestion": "Không tìm thấy kết quả cụ thể. Nhưng đây là những quán nổi tiếng nhất trong thành phố. Có quán nào hợp không?",
            "action": "suggest_popular",
            "new_params": new_params,
            "explanation": "Gợi ý những quán được đánh giá cao nhất",
            "confidence": 0.5,
        }
    
    @staticmethod
    def format_recovery_message(recovery_result: Dict) -> str:
        """Format recovery suggestion for user."""
        if recovery_result["status"] == "no_recovery":
            return recovery_result["suggestion"]
        
        message = recovery_result["suggestion"]
        
        # Add explanation if helpful
        if recovery_result.get("explanation"):
            message += f"\n\n_Gợi ý: {recovery_result['explanation']}_"
        
        return message


class FallbackResponseGenerator:
    """Generate helpful fallback responses."""
    
    @staticmethod
    def generate_clarification_prompt(
        contradictions: List[str],
        ambiguities: List[str],
        original_query: str
    ) -> str:
        """Generate clarification questions."""
        prompts = []
        
        # For contradictions
        if "cheap_expensive" in contradictions:
            prompts.append("Bạn ưu tiên giá rẻ hay chất lượng hơn?")
        
        if "quality_price" in contradictions:
            prompts.append("Bạn muốn quán xịn hay rẻ? Nếu cả hai được thì mở rộng nên ưu tiên cái nào?")
        
        # For ambiguities
        if "vague_cuisine" in ambiguities:
            prompts.append("Bạn muốn ăn gì cụ thể? (phở, bánh mì, cơm, hải sản, ...)")
        
        if "vague_location" in ambiguities:
            prompts.append("Bạn muốn tìm quán ở quận nào? Hay ở gần vị trí hiện tại?")
        
        if "vague_price" in ambiguities:
            prompts.append("Ngân sách dự kiến của bạn là bao nhiêu?")
        
        if not prompts:
            return "Bạn có thể cung cấp thêm thông tin để tôi tìm kiếm chính xác hơn không?"
        
        return "\n".join([f"❓ {p}" for p in prompts])
    
    @staticmethod
    def generate_explanation_for_results(
        query: str,
        params: Dict,
        results: List,
        sub_intents: List
    ) -> str:
        """Generate explanation of why these results were returned."""
        explanation = "Tìm kiếm dựa trên:\n"
        
        # List search criteria
        criteria = []
        
        if params.get('cuisines'):
            criteria.append(f"- Loại món: {', '.join(params['cuisines'])}")
        
        if params.get('max_budget'):
            criteria.append(f"- Giá tối đa: {params['max_budget']:,}đ")
        
        if params.get('max_distance'):
            criteria.append(f"- Bán kính: {params['max_distance']}km")
        
        if params.get('filter_open'):
            criteria.append("- Đang mở cửa")
        
        if params.get('group_size'):
            criteria.append(f"- Nhóm {params['group_size']} người")
        
        explanation += "\n".join(criteria) if criteria else "- Quán ăn chất lượng"
        
        if results:
            explanation += f"\n\n✅ Tìm thấy {len(results)} quán phù hợp, xếp hạng theo:"
            explanation += "\n- Độ liên quan (khớp với yêu cầu)"
            explanation += "\n- Đánh giá (rating)"
            explanation += "\n- Khoảng cách (nếu có vị trí)"
        
        return explanation


# Export
__all__ = [
    'ErrorRecoveryEngine',
    'FallbackResponseGenerator',
]
