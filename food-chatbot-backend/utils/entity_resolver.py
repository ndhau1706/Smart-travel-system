"""
Entity Reference Resolution - Understand references like "quán đó", "quán đầu tiên", "cái thứ 2"
Tracks mentioned entities in conversation and resolves pronouns/references
"""
from typing import Dict, List, Optional, Any
import re
import copy  # BUG #7 FIX: For thread-safe deepcopy
import threading  # BUG #7 FIX: For thread-safe access


class EntityReferenceResolver:
    """Resolve entity references in conversation context."""
    
    # BUG #10 FIX: Maximum recursion depth to prevent stack overflow
    # BUG #CRITICAL-6 FIX: Lower limit from 10 to 5 to prevent complex nested attacks
    MAX_RESOLUTION_DEPTH = 5
    # Maximum conversation history depth to prevent memory exhaustion
    MAX_CONTEXT_DEPTH = 100
    # BUG #CRITICAL-6 FIX: Hard cap on resolution chain size to prevent memory leak
    MAX_CHAIN_SIZE = 100
    
    def __init__(self):
        # BUG #10 FIX: Track resolution chain to detect circular references
        # BUG #CRITICAL-6 FIX: Use set for O(1) lookup and better collision handling
        self._resolution_chain = set()
        
        # BUG #7 FIX: Track context versions to detect stale references
        self._context_versions = {}  # {session_id: version}
        self._version_lock = threading.Lock()  # Thread-safe version tracking
        
        # Reference patterns
        self.reference_patterns = {
            'ordinal': [
                r'quán\s+(?:thứ|số)\s*(\d+)',
                r'cái\s+(?:thứ|số)\s*(\d+)',
                r'nhà\s+hàng\s+(?:thứ|số)\s*(\d+)',
                r'(?:thứ|số)\s*(\d+)',
                r'quán\s+thứ\s+(nhất|hai|ba|bốn|năm)',  # BUG #7 FIX: "quán thứ nhất"
                r'cái\s+thứ\s+(nhất|hai|ba|bốn|năm)',
                r'quán\s+(đầu|đầu\s+tiên|một|hai|ba|bốn|năm)',
                r'cái\s+(đầu|đầu\s+tiên|một|hai|ba|bốn|năm)',
                r'quán\s+(cuối|cuối\s+cùng)',  # Bug 13: "quán cuối"
                r'cái\s+(cuối|cuối\s+cùng)',
            ],
            'demonstrative': [
                r'quán\s+(?:này|đó|kia|nọ|ấy)',
                r'cái\s+(?:này|đó|kia|nọ|ấy)',
                r'nhà\s+hàng\s+(?:này|đó|kia|nọ|ấy)',
                r'(?:nó|it|that|this)',
            ],
            'previous': [
                r'quán\s+(?:trước|trước\s+đó|vừa\s+rồi|nãy|nãy\s+giờ)',
                r'cái\s+(?:trước|trước\s+đó|vừa\s+rồi|nãy|nãy\s+giờ)',
                r'(?:previous|last|earlier)',
            ],
            'multiple': [  # Bug 13: "so sánh 2 quán đầu"
                r'(\d+)\s+quán\s+(đầu|đầu\s+tiên)',
                r'(\d+)\s+cái\s+(đầu|đầu\s+tiên)',
                r'so\s+sánh.*?(\d+)\s+quán',
            ],
            'specific_name': [
                r'quán\s+([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+)',
            ],
            'comparative': [
                r'(?:rẻ|đắt|xa|gần|tốt|xấu)\s+hơn',
                r'(?:cheaper|more expensive|farther|nearer|better|worse)\s+than',
            ],
            'range': [  # BUG #7 FIX: Support range references
                r'quán\s+từ\s+(\d+)\s+đến\s+(\d+)',
                r'cái\s+từ\s+(\d+)\s+đến\s+(\d+)',
                r'from\s+(\d+)\s+to\s+(\d+)',
            ]
        }
        
        # Number word mapping
        self.number_words = {
            'đầu': 1, 'đầu tiên': 1, 'một': 1, 'first': 1, 'nhất': 1,  # BUG #7 FIX: Add 'nhất'
            'hai': 2, 'second': 2,
            'ba': 3, 'third': 3,
            'bốn': 4, 'fourth': 4, 'tư': 4,
            'năm': 5, 'fifth': 5,
            'sáu': 6, 'sixth': 6,
            'bảy': 7, 'seventh': 7,
            'tám': 8, 'eighth': 8,
            'chín': 9, 'ninth': 9,
            'mười': 10, 'tenth': 10,
            # FIXED Bug #25: Support negative indexing
            'cuối': -1, 'cuối cùng': -1, 'last': -1,
        }
        
        # FIXED Bug #25: Support "from end" patterns
        # "quán cuối thứ 2" = 2nd to last = -2
        # "3 quán cuối" = last 3
        self.from_end_patterns = [
            r'quán\s+cuối\s+(?:thứ|số)\s*(\d+)',  # "quán cuối thứ 2" → -2
            r'cái\s+cuối\s+(?:thứ|số)\s*(\d+)',
            r'(\d+)\s+quán\s+cuối',  # "3 quán cuối" → last 3
            r'(\d+)\s+cái\s+cuối',
        ]
    
    def detect_reference(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Detect if query contains entity reference.
        
        Args:
            query: User query
            
        Returns:
            Reference info or None
        """
        query_lower = query.lower()
        
        # FIXED Bug #25: Check "from end" patterns first
        # "quán cuối thứ 2" → -2, "3 quán cuối" → last 3
        for pattern in self.from_end_patterns:
            match = re.search(pattern, query_lower)
            if match:
                num = int(match.group(1))
                
                # Determine if it's "Nth from end" or "last N"
                if 'cuối thứ' in query_lower or 'cuối số' in query_lower:
                    # "quán cuối thứ 2" → 2nd to last → index -2
                    return {
                        'type': 'ordinal',
                        'index': -num,
                        'raw_match': match.group(0)
                    }
                else:
                    # "3 quán cuối" → last 3 restaurants → multiple
                    return {
                        'type': 'multiple_from_end',
                        'count': num,
                        'raw_match': match.group(0)
                    }
        
        # Bug 13: Check multiple references (so sánh 2 quán đầu)
        for pattern in self.reference_patterns.get('multiple', []):
            match = re.search(pattern, query_lower)
            if match:
                count = int(match.group(1))
                return {
                    'type': 'multiple',
                    'count': count,
                    'indices': list(range(count)),  # [0, 1] for "2 quán đầu"
                    'raw_match': match.group(0)
                }
        
        # BUG #7 FIX: Check range references first (quán từ 3 đến 7)
        for pattern in self.reference_patterns.get('range', []):
            match = re.search(pattern, query_lower)
            if match:
                start = int(match.group(1))
                end = int(match.group(2))
                
                # BUG #7 FIX: Validate zero index
                if start == 0 or end == 0:
                    return {
                        'type': 'error',
                        'error': 'invalid_index',
                        'message': 'Số thứ tự phải bắt đầu từ 1 (không phải 0).',
                        'raw_match': match.group(0)
                    }
                
                # BUG #7 FIX: Validate range order
                if start > end:
                    return {
                        'type': 'error',
                        'error': 'invalid_range',
                        'message': f'Khoảng không hợp lệ: {start} đến {end}. Số bắt đầu phải nhỏ hơn số kết thúc.',
                        'raw_match': match.group(0)
                    }
                
                return {
                    'type': 'range',
                    'start': start - 1,  # Convert to 0-indexed
                    'end': end,  # Exclusive end for Python slicing
                    'count': end - start + 1,
                    'raw_match': match.group(0)
                }
        
        # Check ordinal references (quán thứ 2, cái đầu tiên, quán cuối)
        for pattern in self.reference_patterns['ordinal']:
            match = re.search(pattern, query_lower)
            if match:
                # Extract number
                if match.group(1).isdigit():
                    num = int(match.group(1))
                    
                    # BUG #7 FIX: Reject zero index (Vietnamese is 1-indexed)
                    if num == 0:
                        return {
                            'type': 'error',
                            'error': 'invalid_index',
                            'message': 'Số thứ tự phải bắt đầu từ 1 (không phải 0).',
                            'raw_match': match.group(0)
                        }
                    
                    index = num - 1  # Convert to 0-indexed
                else:
                    # Word number
                    word = match.group(1).strip()
                    number = self.number_words.get(word, 1)  # Default to 1 if not found
                    # Convert to 0-indexed: number 1 → index 0, number -1 (last) → index -1
                    index = number - 1 if number > 0 else number
                
                return {
                    'type': 'ordinal',
                    'index': index,
                    'raw_match': match.group(0)
                }
        
        # Check demonstrative (quán này, cái đó)
        for pattern in self.reference_patterns['demonstrative']:
            if re.search(pattern, query_lower):
                return {
                    'type': 'demonstrative',
                    'index': 0,  # Usually refers to most recently mentioned
                    'raw_match': re.search(pattern, query_lower).group(0),
                    'is_ambiguous': 'kia' in query_lower  # Bug 13: "quán kia" is ambiguous
                }
        
        # Check previous reference
        for pattern in self.reference_patterns['previous']:
            if re.search(pattern, query_lower):
                return {
                    'type': 'previous',
                    'index': 0,
                    'raw_match': re.search(pattern, query_lower).group(0)
                }
        
        # Check comparative
        for pattern in self.reference_patterns['comparative']:
            if re.search(pattern, query_lower):
                return {
                    'type': 'comparative',
                    'raw_match': re.search(pattern, query_lower).group(0)
                }
        
        return None
    
    def resolve_reference(
        self, 
        query: str,
        conversation_context: Dict[str, Any],
        _depth: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve entity reference to actual entity.
        
        Args:
            query: User query with reference
            conversation_context: Previous conversation data
            _depth: Current recursion depth (internal parameter)
            
        Returns:
            Resolved entity or None
        """
        # BUG #10 FIX: Handle None query
        if query is None:
            return {
                'type': 'error',
                'error': 'invalid_query',
                'message': 'Câu hỏi không hợp lệ.'
            }
        
        # BUG #CRITICAL-6 FIX: Early depth check BEFORE any processing
        if _depth >= self.MAX_RESOLUTION_DEPTH:
            # Clear chain on depth exceeded
            self._resolution_chain.clear()
            return {
                'type': 'error',
                'error': 'max_depth_exceeded',
                'message': 'Câu hỏi quá phức tạp. Vui lòng đơn giản hóa yêu cầu của bạn.'
            }
        
        # BUG #CRITICAL-6 FIX: Better hash with salt to prevent collision attacks
        import hashlib
        # Include depth in hash to prevent same query at different levels from colliding
        query_normalized = query.lower().strip()
        query_hash = hashlib.sha256(
            (query_normalized + str(_depth)).encode('utf-8')
        ).hexdigest()
        
        # BUG #CRITICAL-6 FIX: Circular detection BEFORE processing (early exit)
        if query_hash in self._resolution_chain:
            # Clear chain on circular detection
            self._resolution_chain.clear()
            return {
                'type': 'error',
                'error': 'circular_reference',
                'message': 'Câu hỏi của bạn tạo vòng lặp. Vui lòng hỏi rõ ràng hơn.'
            }
        
        # BUG #CRITICAL-6 FIX: Hard limit chain size to prevent memory leak
        if len(self._resolution_chain) >= self.MAX_CHAIN_SIZE:
            # Keep only last 50 entries to prevent unbounded growth
            # Convert to list, slice, convert back to set
            chain_list = list(self._resolution_chain)
            self._resolution_chain = set(chain_list[-50:])
        
        # Add current query to resolution chain
        self._resolution_chain.add(query_hash)
        
        reference = self.detect_reference(query)
        if not reference:
            # BUG #CRITICAL-6 FIX: Remove current query from chain when no reference
            self._resolution_chain.discard(query_hash)
            return None
        
        # BUG #7 FIX: Early error detection for invalid references
        if reference.get('type') == 'error':
            self._resolution_chain.discard(query_hash)
            return reference
        
        # Get previously mentioned restaurants
        last_restaurants = conversation_context.get('last_restaurants', [])
        
        # BUG #10 FIX: Validate last_restaurants type
        # Treat None and non-list as "no_context" (user hasn't searched yet)
        if not isinstance(last_restaurants, list):
            self._resolution_chain.clear()
            return {
                'type': 'error',
                'error': 'no_context',
                'message': 'Bạn chưa tìm kiếm quán nào. Hãy tìm kiếm trước nhé!'
            }
        
        # BUG #7 FIX: Thread-safe deepcopy to prevent concurrent modification
        last_restaurants = copy.deepcopy(last_restaurants)
        
        # BUG #7 FIX: Validate context version to detect stale references
        session_id = conversation_context.get('session_id', 'unknown')
        current_version = conversation_context.get('context_version', 0)
        
        with self._version_lock:
            stored_version = self._context_versions.get(session_id, None)
            
            # BUG #7 FIX: If session was invalidated (not in dict), reject reference
            if stored_version is None and current_version > 0:
                # Session was deleted/invalidated
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'stale_reference',
                    'message': 'Kết quả tìm kiếm đã thay đổi. Vui lòng tìm kiếm lại.'
                }
            
            # If version mismatch, context was invalidated
            if stored_version is not None and current_version != stored_version:
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'stale_reference',
                    'message': 'Kết quả tìm kiếm đã thay đổi. Vui lòng tìm kiếm lại.'
                }
            
            # Update stored version if first time or valid
            if stored_version is None:
                self._context_versions[session_id] = current_version
        
        # BUG #10 FIX: Validate conversation context depth
        conversation_history = conversation_context.get('turns', [])
        if len(conversation_history) > self.MAX_CONTEXT_DEPTH:
            # Trim old history to prevent memory exhaustion
            conversation_context['turns'] = conversation_history[-self.MAX_CONTEXT_DEPTH:]
        
        if not last_restaurants:
            # Bug 13: No context available
            # Clear resolution chain on error
            self._resolution_chain.clear()
            return {
                'type': 'error',
                'error': 'no_context',
                'message': 'Bạn chưa tìm kiếm quán nào. Hãy tìm kiếm trước nhé!'
            }
        
        ref_type = reference['type']
        
        # Bug 13: Handle ambiguous demonstrative (quán kia)
        if ref_type == 'demonstrative' and reference.get('is_ambiguous'):
            # BUG #10 FIX: Clear resolution chain on error
            self._resolution_chain.clear()
            return {
                'type': 'error',
                'error': 'ambiguous_reference',
                'message': 'Bạn nói quán nào? Bạn có thể nói "quán đầu tiên" hoặc "quán thứ 2".'
            }
        
        # FIXED Bug #25: Handle "last N" references (3 quán cuối)
        if ref_type == 'multiple_from_end':
            count = reference['count']
            
            # BUG #10 FIX: Limit count to prevent excessive memory usage
            if count > 50:
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'excessive_count',
                    'message': f'Không thể xử lý quá 50 quán cùng lúc. Bạn yêu cầu {count} quán.'
                }
            
            if count > len(last_restaurants):
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'out_of_range',
                    'message': f'Bạn chỉ có {len(last_restaurants)} quán, không đủ {count} quán cuối.'
                }
            # Get last N restaurants
            restaurants = last_restaurants[-count:]
            # BUG #10 FIX: Clear chain on successful resolution
            self._resolution_chain.clear()
            return {
                'type': 'multiple_restaurants',
                'data': restaurants,
                'count': count,
                'reference_text': reference['raw_match'],
                'resolved_names': [r.get('name', 'Unknown') for r in restaurants],
                'resolution_depth': _depth
            }
        
        # BUG #7 FIX: Handle range references (quán từ 3 đến 7)
        if ref_type == 'range':
            start = reference['start']
            end = reference['end']
            count = reference['count']
            
            # BUG #7 FIX: Validate range bounds
            if start >= len(last_restaurants):
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'out_of_range',
                    'message': f'Bạn chỉ có {len(last_restaurants)} quán. "Quán thứ {start + 1}" không tồn tại.'
                }
            
            if end > len(last_restaurants):
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'out_of_range',
                    'message': f'Bạn chỉ có {len(last_restaurants)} quán. Khoảng yêu cầu vượt quá giới hạn.'
                }
            
            # Get restaurants in range
            restaurants = last_restaurants[start:end]
            self._resolution_chain.clear()
            return {
                'type': 'multiple_restaurants',
                'data': restaurants,
                'count': len(restaurants),
                'reference_text': reference['raw_match'],
                'resolved_names': [r.get('name', 'Unknown') for r in restaurants],
                'resolution_depth': _depth
            }
        
        # Bug 13: Handle multiple references (so sánh 2 quán đầu)
        if ref_type == 'multiple':
            count = reference['count']
            indices = reference['indices']
            
            # BUG #10 FIX: Limit count to prevent excessive memory usage
            if count > 50:
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'excessive_count',
                    'message': f'Không thể so sánh quá 50 quán cùng lúc. Bạn yêu cầu {count} quán.'
                }
            
            if all(0 <= idx < len(last_restaurants) for idx in indices):
                restaurants = [last_restaurants[idx] for idx in indices]
                # BUG #10 FIX: Clear chain on successful resolution
                self._resolution_chain.clear()
                return {
                    'type': 'multiple_restaurants',
                    'data': restaurants,
                    'count': count,
                    'reference_text': reference['raw_match'],
                    'resolved_names': [r.get('name', 'Unknown') for r in restaurants],
                    'resolution_depth': _depth
                }
            else:
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'out_of_range',
                    'message': f'Bạn chỉ có {len(last_restaurants)} quán trong kết quả tìm kiếm.'
                }
        
        if ref_type in ['ordinal', 'demonstrative', 'previous']:
            index = reference['index']
            
            # FIXED Bug #25: Proper negative index handling with bounds check
            if index < 0:
                # Negative index: -1 = last, -2 = 2nd to last, etc.
                actual_index = len(last_restaurants) + index
                
                # Check if out of bounds
                if actual_index < 0:
                    # e.g., -5 on list of 3 items
                    self._resolution_chain.clear()
                    return {
                        'type': 'error',
                        'error': 'out_of_range',
                        'message': f'Bạn chỉ có {len(last_restaurants)} quán. Không có "quán cuối thứ {abs(index)}".'
                    }
                index = actual_index
            
            # FIXED Bug #25: Bounds check for positive index
            if 0 <= index < len(last_restaurants):
                restaurant = last_restaurants[index]
                # BUG #10 FIX: Clear chain on successful resolution
                self._resolution_chain.clear()
                return {
                    'type': 'restaurant',
                    'data': restaurant,
                    'reference_text': reference['raw_match'],
                    'resolved_name': restaurant.get('name', 'Unknown'),
                    'resolution_depth': _depth
                }
            else:
                self._resolution_chain.clear()
                return {
                    'type': 'error',
                    'error': 'out_of_range',
                    'message': f'Bạn chỉ có {len(last_restaurants)} quán trong kết quả tìm kiếm.'
                }
        
        elif ref_type == 'comparative':
            # For comparative, return the reference restaurant (usually first one)
            if last_restaurants:
                # BUG #10 FIX: Clear chain on successful resolution
                self._resolution_chain.clear()
                return {
                    'type': 'comparative',
                    'reference_restaurant': last_restaurants[0],
                    'reference_text': reference['raw_match'],
                    'resolution_depth': _depth
                }
        
        # BUG #10 FIX: Clear chain when no resolution
        self._resolution_chain.clear()
        return None
    
    def extract_action_from_reference_query(self, query: str) -> Optional[str]:
        """
        Extract what user wants to do with referenced entity.
        
        Args:
            query: Query with reference
            
        Returns:
            Action type or None
        """
        query_lower = query.lower()
        
        # Check for common actions
        actions = {
            'check_status': [
                'đóng cửa', 'mở cửa', 'có mở', 'closed', 'open',
                'giờ mở', 'opening hours', 'thời gian'
            ],
            'check_price': [
                'giá', 'bao nhiêu', 'price', 'cost', 'how much',
                'đắt', 'rẻ', 'expensive', 'cheap'
            ],
            'check_location': [
                'ở đâu', 'địa chỉ', 'where', 'location', 'address',
                'xa', 'gần', 'far', 'near', 'khoảng cách', 'distance'
            ],
            'check_rating': [
                'rating', 'đánh giá', 'review', 'có ngon', 'tốt không',
                'good', 'quality'
            ],
            'get_details': [
                'chi tiết', 'thông tin', 'details', 'info', 'about',
                'cho tôi biết', 'tell me'
            ],
            'compare': [
                'so sánh', 'compare', 'khác gì', 'difference',
                'hơn', 'better', 'worse'
            ],
            'book': [
                'đặt', 'book', 'reservation', 'chỗ', 'bàn'
            ]
        }
        
        for action_type, keywords in actions.items():
            if any(keyword in query_lower for keyword in keywords):
                return action_type
        
        return 'get_details'  # Default action
    
    def generate_reference_response(
        self,
        query: str,
        resolved_entity: Dict[str, Any],
        action: str,
        language: str = 'vi'
    ) -> str:
        """
        Generate response based on resolved reference and action.
        
        Args:
            query: Original query
            resolved_entity: Resolved entity data
            action: Action to perform
            language: Response language
            
        Returns:
            Response message
        """
        restaurant = resolved_entity.get('data', {})
        name = restaurant.get('name', 'Unknown')
        
        if action == 'check_status':
            is_open = restaurant.get('is_open', False)
            status = restaurant.get('open_status', '')
            if language == 'vi':
                return f"🏪 **{name}**\n\n{'✅ Đang mở cửa' if is_open else '🔴 Đã đóng cửa'}\n{status}"
            else:
                return f"🏪 **{name}**\n\n{'✅ Currently open' if is_open else '🔴 Closed'}\n{status}"
        
        elif action == 'check_price':
            price_level = restaurant.get('price_level', '')
            if language == 'vi':
                price_map = {
                    'PRICE_LEVEL_INEXPENSIVE': 'Bình dân (< 100k/người)',
                    'PRICE_LEVEL_MODERATE': 'Trung bình (100-200k/người)',
                    'PRICE_LEVEL_EXPENSIVE': 'Cao cấp (200-500k/người)',
                    'PRICE_LEVEL_VERY_EXPENSIVE': 'Sang trọng (> 500k/người)'
                }
                return f"🏪 **{name}**\n\n💰 Giá: {price_map.get(price_level, 'Chưa có thông tin')}"
            else:
                price_map = {
                    'PRICE_LEVEL_INEXPENSIVE': 'Budget-friendly (< 100k/person)',
                    'PRICE_LEVEL_MODERATE': 'Moderate (100-200k/person)',
                    'PRICE_LEVEL_EXPENSIVE': 'Upscale (200-500k/person)',
                    'PRICE_LEVEL_VERY_EXPENSIVE': 'Luxury (> 500k/person)'
                }
                return f"🏪 **{name}**\n\n💰 Price: {price_map.get(price_level, 'Not available')}"
        
        elif action == 'check_location':
            address = restaurant.get('address', 'Chưa có thông tin')
            distance = restaurant.get('distance_text', '')
            if language == 'vi':
                return f"🏪 **{name}**\n\n📍 Địa chỉ: {address}\n{distance}"
            else:
                return f"🏪 **{name}**\n\n📍 Address: {address}\n{distance}"
        
        elif action == 'check_rating':
            rating = restaurant.get('rating', 0)
            rating_count = restaurant.get('rating_count', 0)
            if language == 'vi':
                return f"🏪 **{name}**\n\n⭐ Đánh giá: {rating}/5 ({rating_count} reviews)"
            else:
                return f"🏪 **{name}**\n\n⭐ Rating: {rating}/5 ({rating_count} reviews)"
        
        else:  # get_details
            rating = restaurant.get('rating', 0)
            price_level = restaurant.get('price_level', '')
            address = restaurant.get('address', '')
            phone = restaurant.get('phone', '')
            
            if language == 'vi':
                return f"🏪 **{name}**\n\n⭐ {rating}/5\n💰 {price_level}\n📍 {address}\n📞 {phone}"
            else:
                return f"🏪 **{name}**\n\n⭐ {rating}/5\n💰 {price_level}\n📍 {address}\n📞 {phone}"


    def update_context_version(self, session_id: str, new_version: int):
        """
        BUG #7 FIX: Update context version when restaurants list changes.
        This invalidates old references to prevent stale data access.
        
        Args:
            session_id: Session identifier
            new_version: New context version number
        """
        with self._version_lock:
            self._context_versions[session_id] = new_version
    
    def invalidate_context(self, session_id: str):
        """
        BUG #7 FIX: Invalidate context for a session.
        Forces re-search before references can be used.
        
        Args:
            session_id: Session identifier
        """
        with self._version_lock:
            if session_id in self._context_versions:
                del self._context_versions[session_id]


# Global instance
entity_resolver = EntityReferenceResolver()
