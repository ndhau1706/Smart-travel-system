"""
RAG (Retrieval Augmented Generation) pipeline.
Enhanced with advanced NLP modules for better understanding.
"""
from typing import Dict, Any, Optional, List
from deep_translator import GoogleTranslator
from config import settings
from utils import (
    detect_language,
    is_food_related,
    extract_price_range,
    extract_location,
    detect_cuisine_type,
    detect_atmosphere,
    normalize_text,
    # Advanced modules
    normalize_advanced,
    intent_classifier,
    IntentType,
    semantic_engine,
    ErrorRecoveryEngine,
    FallbackResponseGenerator
)
from services.hybrid_search import hybrid_search
from services.ollama_service import ollama_service
from services.cache_service import cache_service


class RAGPipeline:
    """RAG pipeline: gatekeeper → extract_params → embedding → hybrid_search → ranking → generate"""
    
    def __init__(self):
        self.translator_vi = GoogleTranslator(source='auto', target='vi')
        self.translator_en = GoogleTranslator(source='auto', target='en')
    
    async def process(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user query through RAG pipeline with enhanced features.
        
        Args:
            query: User query
            user_context: Additional user context (location, preferences)
            
        Returns:
            Response dictionary with enriched restaurant data
        """
        from utils import (
            detect_group_size, is_restaurant_open, calculate_distance, 
            format_distance, calculate_trending_score, get_restaurant_badges,
            analyze_review_sentiment, extract_signature_dishes, format_review_insights,
            is_group_friendly
        )
        
        # Step 0: Advanced input normalization (typos, slang, code-switching)
        normalized_query = normalize_advanced(query)
        
        # Step 1: Language detection
        language = detect_language(normalized_query)
        
        # Step 1.5: Intent classification with off-topic detection
        intent_result = intent_classifier.classify(normalized_query)
        
        # Handle OFF_TOPIC queries (hospitals, tourism, etc)
        if intent_result['main_intent'] == IntentType.OFF_TOPIC:
            return self._generate_off_topic_response(language)
        
        # Handle GREETING
        if intent_result['main_intent'] == IntentType.GREETING:
            return self._generate_greeting_response(language)
        
        # Handle contradictions - ask for clarification
        if intent_result['has_contradiction']:
            clarification = FallbackResponseGenerator.generate_clarification_prompt(
                intent_result['contradiction_types'],
                intent_result['ambiguity_types'] if intent_result['is_ambiguous'] else [],
                normalized_query
            )
            return {
                "message": clarification,
                "restaurants": [],
                "restaurant_count": 0,
                "language": language,
                "needs_clarification": True,
                "intent_analysis": intent_result
            }
        
        # Fallback check for food-related (in case intent classifier missed)
        if not is_food_related(normalized_query, language):
            return self._generate_off_topic_response(language)
        
        # Check cache first (use original query for cache key)
        # Skip cache if user_location provided (dynamic results)
        user_location = user_context.get('user_location') if user_context else None
        if not user_location:
            cached_result = await cache_service.get(query, language)
            if cached_result:
                return cached_result
        
        # Step 2: Extract parameters from normalized query
        params = self._extract_parameters(normalized_query, language)
        
        # Step 2.5: Detect additional context
        group_size = detect_group_size(normalized_query)
        if group_size:
            params['group_size'] = group_size
        
        # Check if user wants open restaurants NOW
        time_keywords = ['mở cửa', 'đang mở', 'open now', 'currently open', 'mở bây giờ']
        filter_by_open = any(keyword in normalized_query.lower() for keyword in time_keywords)
        if filter_by_open:
            params['filter_open'] = True
        
        # Check if query has location-related keywords that need user location
        location_needed_keywords = ['gần đây', 'gần tôi', 'gần chỗ tôi', 'nearby', 'near me', 'gần nhất']
        query_needs_location = any(kw in normalized_query.lower() for kw in location_needed_keywords)
        
        # If query needs location but user hasn't shared, warn them
        if query_needs_location and not user_location:
            # Still search but add note about location
            params['needs_location_warning'] = True
        
        # Step 3: Hybrid search with extracted parameters
        # Get more candidates before filtering to ensure enough results
        search_top_k = 50  # Get 50 candidates then filter
        restaurants = await hybrid_search.search(
            query=normalized_query,
            top_k=search_top_k,
            filters=params
        )
        
        # Step 3.5: Validate results relevance with IMPROVED filter
        if restaurants:
            restaurants = self._filter_by_food_keywords(restaurants, normalized_query)
        
        # Step 3.6: Enrich restaurants with NEW advanced features
        if restaurants:
            try:
                restaurants = self._enrich_restaurant_data(
                    restaurants, 
                    user_location=user_location,
                    language=language,
                    group_size=group_size,
                    filter_open=filter_by_open
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise
        
        # Step 3.7: DISABLED - Use hybrid search relevance only
        # Advanced ranking can shuffle results incorrectly
        # if restaurants:
        #     restaurants = self._rank_with_advanced_scoring(
        #         restaurants,
        #         params=params,
        #         user_location=user_location
        #     )
        #     # Limit to MAX_RESULTS after ranking
        restaurants = restaurants[:settings.MAX_RESULTS]
        
        # Step 4: Generate response (use normalized query for better understanding)
        if not restaurants:
            response = await self._generate_no_results_response(normalized_query, language, params)
        else:
            response = await self._generate_response_with_results(
                query=normalized_query,
                restaurants=restaurants,
                language=language,
                params=params
            )
        
        # Cache result (if no dynamic location)
        if not user_location:
            await cache_service.set(query, response, language)
        
        # Final safeguard: ensure response is never None
        if response is None:
            return {
                "message": "Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại.",
                "restaurants": [],
                "restaurant_count": 0,
                "language": language
            }
        
        return response
    
    def _clean_search_query(self, query: str) -> str:
        """
        Clean query by removing noise words for better BM25/FAISS search.
        
        Args:
            query: Normalized query
            
        Returns:
            Cleaned query focused on content keywords
        """
        # Remove common noise/stop words
        stop_words = [
            # Vietnamese
            'gợi ý', 'goi y', 'tìm', 'tim', 'cho tôi', 'cho toi',
            'giúp tôi', 'giup toi', 'muốn', 'muon', 'cần', 'can',
            'đi', 'di', 'ăn', 'an', 'quán', 'quan', 'nhà hàng', 'nha hang',
            'chỗ', 'cho', 'nơi', 'noi',
            # English
            'recommend', 'suggest', 'find', 'show', 'give', 'need', 'want',
            'restaurant', 'place', 'where'
        ]
        
        words = query.lower().split()
        # Keep important keywords like food types, location, price, rating
        cleaned_words = [w for w in words if w not in stop_words]
        
        # If everything removed, return original (safety)
        if not cleaned_words:
            return query
        
        return ' '.join(cleaned_words)
    
    def _extract_parameters(self, query: str, language: str) -> Dict[str, Any]:
        """
        Extract search parameters from query.
        
        Args:
            query: User query
            language: Detected language
            
        Returns:
            Dictionary of extracted parameters
        """
        params = {}
        
        # Extract distance information FIRST (to avoid confusion with price)
        from utils.text_processing import extract_distance
        distance_info = extract_distance(query)
        if distance_info.get('value'):
            params['max_distance'] = distance_info['value']
        
        # Extract price information (now safer from km confusion)
        price_info = extract_price_range(query)
        if price_info.get('level'):
            params['price_level'] = price_info['level']
        if price_info.get('max'):
            # Double-check: don't set max_budget if query is about distance
            query_lower = query.lower()
            is_distance_query = any(kw in query_lower for kw in [
                'km', 'khoảng cách', 'bán kính', 'gần', 'xa',
                'distance', 'radius', 'near', 'far'
            ])
            if not is_distance_query:
                params['max_budget'] = price_info['max']
        
        # Extract location
        locations = extract_location(query)
        if locations:
            params['locations'] = locations
        
        # Extract cuisine types
        cuisines = detect_cuisine_type(query)
        if cuisines:
            params['cuisines'] = cuisines
        
        # Extract atmosphere preferences
        atmosphere = detect_atmosphere(query)
        if atmosphere:
            params['atmosphere'] = atmosphere
        
        # Extract rating preference (enhanced with slang)
        rating_keywords = ['ngon', 'nổi tiếng', 'famous', 'delicious', 'good', 
                          'đánh giá cao', 'đánh giá tốt', 'rating cao', 'rating tốt',
                          'review tốt', 'review cao', 'highly rated',
                          'được đánh giá', 'chất lượng', 'uy tín',
                          # Slang (after teencode normalization)
                          'chất', 'top', 'xỉu', 'bá']
        if any(word in query.lower() for word in rating_keywords):
            params['min_rating'] = 4.0
        
        # Extract price preference keywords (enhanced with slang)
        cheap_keywords = ['rẻ', 'bình dân', 'giá rẻ', 'cheap', 'budget', 'affordable',
                         'tiết kiệm', 'phải chăng',
                         # Slang (after teencode normalization)
                         'mềm', 'bèo', 'vài trăm', 'vài chục']
        
        # Context-aware budget adjustment
        # Check if atmosphere suggests special occasion (romantic, luxury, etc.)
        has_special_atmosphere = (
            params.get('atmosphere') and 
            any(atmo in ['romantic', 'luxury'] for atmo in params['atmosphere'])
        )
        
        # Only set budget if explicitly mentioned with price keywords
        explicit_cheap_keywords = ['rẻ nhất', 'giá rẻ', 'giá bình dân', 'cheapest']
        if any(word in query.lower() for word in explicit_cheap_keywords) and not params.get('max_budget'):
            # Only for EXPLICIT cheap requests
            params['max_budget'] = 150000  # Reasonable budget for "cheap"
        
        return params
    
    def _filter_by_food_keywords(
        self,
        restaurants: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        IMPROVED filter: Keep restaurants whose NAME matches food keywords in query.
        Simple, reliable, no threshold-based scoring.
        
        Args:
            restaurants: List of restaurants from hybrid search
            query: User query (normalized)
            
        Returns:
            Filtered list of relevant restaurants
        """
        try:
            from utils.text_processing import strip_accents
            
            query_lower = strip_accents(query.lower())
            
            # Extract food keywords from query
            # Common Vietnamese food types
            food_keywords = {
            # Dishes
            'pho': ['pho', 'phở'],
            'bun': ['bun', 'bún'],
            'com': ['com', 'cơm', 'rice'],
            'banh_mi': ['banh mi', 'bánh mì', 'banh', 'bánh'],
            'mi': ['mi', 'mì', 'noodle'],
            'lau': ['lau', 'lẩu', 'hotpot', 'hot pot'],
            'nuong': ['nuong', 'nướng', 'grill', 'bbq', 'barbe'],
            'hai_san': ['hai san', 'hải sản', 'seafood', 'oc', 'tôm', 'cua'],
            'ga': ['ga', 'gà', 'chicken'],
            'bo': ['bo', 'bò', 'beef'],
            'heo': ['heo', 'heo', 'pork', 'lon'],
            'buffet': ['buffet', 'buffet'],
            'sushi': ['sushi', 'sashimi', 'japanese'],
            'pizza': ['pizza', 'italy', 'ý'],
            'cafe': ['cafe', 'cà phê', 'coffee', 'ca phe'],
            'tra': ['tra', 'trà', 'tea', 'tra sua', 'trà sữa'],
            'chay': ['chay', 'vegetarian', 'vegan'],
            'nem': ['nem', 'spring roll', 'cha gio'],
            'hu_tieu': ['hu tieu', 'hủ tiếu'],
            'banh_xeo': ['banh xeo', 'bánh xèo'],
            'bun_cha': ['bun cha', 'bún chả'],
                'com_tam': ['com tam', 'cơm tấm'],
            }
            
            # Find which food types are mentioned in query
            mentioned_foods = []
            for food_type, variants in food_keywords.items():
                for variant in variants:
                    variant_normalized = strip_accents(variant.lower())
                    if variant_normalized in query_lower:
                        mentioned_foods.append(food_type)
                        break
            
            # If no specific food mentioned, it might be location/price query → return all
            if not mentioned_foods:
                return restaurants[:settings.MAX_RESULTS]
            
            # Filter: keep restaurants whose name matches ANY mentioned food
            # IMPROVED: If query mentions "coffee", match ALL coffee-related words (cafe, cà phê, coffee)
            filtered = []
            for restaurant in restaurants:
                name_lower = strip_accents(restaurant.get('name', '').lower())
                
                # Check if restaurant name contains any of the mentioned food keywords
                matches = False
                for food_type in mentioned_foods:
                    # Match ANY variant of this food type (not just the one in query)
                    for variant in food_keywords[food_type]:
                        variant_normalized = strip_accents(variant.lower())
                        if variant_normalized in name_lower:
                            matches = True
                            break
                    if matches:
                        break
                
                if matches:
                    filtered.append(restaurant)
            
            # If filter too aggressive (< 2 results) AND we have originals, return originals
            # But log warning
            if len(filtered) < 2 and len(restaurants) >= 5:
                print(f"⚠️ Filter too aggressive: {len(filtered)} results for query '{query[:50]}'")
                print(f"   Returning original {len(restaurants)} restaurants")
                return restaurants[:settings.MAX_RESULTS]
            
            # Return filtered results
            print(f"✓ Filter applied: {len(restaurants)} → {len(filtered)} for query '{query[:50]}'")
            return filtered[:settings.MAX_RESULTS]
            
        except Exception as e:
            print(f"❌ Filter error: {e}")
            # Fallback: return original
            return restaurants[:settings.MAX_RESULTS]
    
    def _filter_relevant_results(
        self,
        restaurants: List[Dict[str, Any]],
        query: str,
        threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Filter out irrelevant results to prevent hallucination.
        Check if restaurant name/tags actually match the query keywords.
        
        Supports TWO modes:
        - AND logic: "lẩu VÀ hải sản" → must have BOTH (default for multiple foods)
        - OR logic: "lẩu HOẶC hải sản" → can have EITHER
        """
        from utils.text_processing import strip_accents, tokenize_vietnamese
        
        # Skip filter for generic queries
        generic_keywords = ['goi y', 'recommend', 'suggest', 'an gi', 'doi bung', 'muon an', 'tu van', 'gioi thieu']
        normalized_query_check = strip_accents(query.lower())
        if any(kw in normalized_query_check for kw in generic_keywords):
            return restaurants[:settings.MAX_RESULTS]
        
        # Extract food keywords from query (including phrases)
        query_lower = strip_accents(query.lower())
        query_tokens = set(tokenize_vietnamese(query_lower))
        
        # Special case: "chay và mặn" or "chay va man" means restaurants with BOTH options
        has_chay_man = ('chay' in query_lower or 'vegetarian' in query_lower) and ('man' in query_lower or 'meat' in query_lower)
        
        # Detect AND vs OR logic
        # OR indicators: "hoặc", "or", "hay là"
        # AND indicators (default): "và", "với", "cùng", "and", or just multiple foods
        use_or_logic = any(word in query_lower for word in ['hoac', 'or', 'hay la', 'hoac la'])
        
        # Expanded food keywords/phrases (Vietnamese + English + slang)
        food_keywords = [
            # Vietnamese dishes
            'pho', 'bun', 'com', 'banh', 'mi', 'lau', 'nuong', 'xao',
            'ga', 'bo', 'heo', 'ca', 'tom', 'cua', 'oc', 'cafe', 'tra',
            'nem', 'cha', 'goi', 'chao', 'sup', 'canh', 'che', 'xoi',
            'hu tieu', 'hutieu', 'kho', 'chien',
            # Restaurant/food establishment keywords
            'quan', 'qua', 'nha hang', 'restaurant', 'an',
            # Seafood
            'hai san', 'haisan', 'seafood', 'fish', 'shrimp', 'crab', 'squid',
            # International
            'sushi', 'pizza', 'pasta', 'burger', 'salad', 'steak',
            'bbq', 'grill', 'buffet', 'hotpot',
            # Drinks
            'bia', 'beer', 'tra sua', 'milk tea', 'coffee', 'nuoc',
            # Special categories
            'chay', 'vegetarian', 'vegan', 'do chay',  # Vegetarian
            # Phrases (multi-word)
            'banh mi', 'bun bo', 'com tam', 'pho bo', 'lau thai',
            'bun cha', 'bun thit', 'mi quang', 'hu tieu', 'tra sua', 'do chay'
        ]
        
        # Check both tokens and full phrases
        query_food_keywords = query_tokens & set(food_keywords)
        
        # Special case: If query is "chay và mặn", only look for "chay"
        # User wants restaurants with vegetarian options (the meat is implied as default)
        if has_chay_man:
            query_food_keywords = {'chay'}  # Only filter by vegetarian tag
        
        # Check for multi-word phrases directly in query
        # Also handle spaced and non-spaced variations
        multi_word_foods = ['banh mi', 'bun bo', 'com tam', 'pho bo', 'bun thit',
                           'hai san', 'lau thai', 'bun cha', 'mi quang']
        for phrase in multi_word_foods:
            phrase_no_space = phrase.replace(' ', '')
            # Check both "hai san" and "haisan" forms
            if phrase in query_lower or phrase_no_space in query_lower.replace(' ', ''):
                query_food_keywords.add(phrase_no_space)
                # Also add individual tokens for partial matching
                for token in phrase.split():
                    if token in food_keywords:
                        query_food_keywords.add(token)
        
        if not query_food_keywords:
            # No specific food keyword, return all (general query like "quán ngon")
            return restaurants[:settings.MAX_RESULTS]
        
        relevant = []
        for restaurant in restaurants:
            # Check name and tags
            name_lower = strip_accents(restaurant.get('name', '').lower()).replace(' ', '')
            
            # Parse food_tags (can be list, JSON string, or plain text)
            tags = restaurant.get('food_tags', '')
            if isinstance(tags, list):
                # Join list items: ["lẩu", "hải sản"] -> "lau hai san"
                tags_text = ' '.join(str(t) for t in tags)
            elif isinstance(tags, str):
                # String: remove JSON brackets if present
                tags_text = tags.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
            else:
                tags_text = ''
            
            tags_lower = strip_accents(tags_text.lower()).replace(' ', '')
            
            combined_text = f"{name_lower} {tags_lower}"
            
            # Find which keywords match this restaurant
            matched_keywords = []
            for keyword in query_food_keywords:
                keyword_no_space = keyword.replace(' ', '')
                # Special handling for "chay" (vegetarian)
                if keyword in ['chay', 'vegetarian', 'vegan', 'dochay']:
                    # Must match "đồ chay" in food_tags exactly
                    if 'đồ chay' in restaurant.get('food_tags', []):
                        matched_keywords.append(keyword)
                elif keyword_no_space in combined_text:
                    matched_keywords.append(keyword)
            
            # Apply AND or OR logic
            if use_or_logic:
                # OR logic: Restaurant must have AT LEAST ONE keyword
                # Example: "lẩu HOẶC hải sản" → quán có lẩu OR hải sản
                match = len(matched_keywords) >= 1
            else:
                # AND logic: Restaurant must have ALL keywords (default)
                # Example: "lẩu VÀ hải sản" → quán phải có cả lẩu VÀ hải sản
                # This is stricter but gives user exactly what they want
                match = len(matched_keywords) == len(query_food_keywords)
            
            if match:
                # Store matched keywords for debugging/ranking
                restaurant['_matched_foods'] = matched_keywords
                restaurant['_match_type'] = 'OR' if use_or_logic else 'AND'
                relevant.append(restaurant)
        
        # Fallback: if filter too aggressive, return original results
        if len(relevant) < 3 and len(restaurants) >= 3:
            return restaurants[:settings.MAX_RESULTS]
        
        # NO FALLBACK for specific food queries - prevent hallucination
        # AND logic example: "lẩu và hải sản" → only return restaurants with BOTH
        # OR logic example: "lẩu hoặc hải sản" → return restaurants with EITHER
        
        return relevant
    
    def _detect_contradiction(self, query: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Detect CLEARLY NONSENSICAL queries and ask for clarification.
        
        Note: We only detect obvious logical contradictions, not valid requests like:
        - "quán chay có thịt" → Valid! User wants mixed menu (vegetarian + meat options)
        - "quán rẻ sang trọng" → Valid! User wants good value (cheap but nice)
        
        We ONLY detect:
        - "bán X nhưng không bán X" → Logical nonsense
        - "buffet miễn phí" → Does not exist
        
        For ambiguous cases, let RAG handle it. If no results found, system will ask naturally.
        """
        from utils.text_processing import strip_accents
        query_lower = strip_accents(query.lower())
        
        # Contradiction Type 1: "Bán X nhưng không bán X" (sells X but doesn't sell X)
        import re
        pattern = r'(ban|phuc vu|co).+?(nhung|ma).+?(khong|ko|k).+?(ban|phuc vu)'
        if re.search(pattern, query_lower):
            if language == "vi":
                message = (
                    "Ơ kìa, có gì đó sai sai 😅\n\n"
                    "Bạn vừa nói **bán** món gì đó nhưng lại nói **không bán** món đó luôn à?\n"
                    "Mình đọc mãi chưa hiểu bạn muốn gì nè! 🤷\n\n"
                    "Bạn có thể nói lại rõ hơn được không:\n"
                    "- Bạn muốn tìm quán bán món **gì**?\n"
                    "- Hay bạn muốn tìm quán **KHÔNG** bán món nào?\n\n"
                    "Nói đơn giản thôi, mình sẽ giúp bạn ngay! 😊"
                )
            else:
                message = (
                    "Wait, something's not right here 😅\n\n"
                    "You said you want a place that **sells** something but also **doesn't sell** it?\n"
                    "I'm confused! 🤷\n\n"
                    "Could you clarify:\n"
                    "- What dish do you want to find?\n"
                    "- Or what dish do you want to **avoid**?\n\n"
                    "Just keep it simple, I'll help you! 😊"
                )
            
            return {
                "message": message,
                "restaurants": [],
                "language": language,
                "needs_clarification": True
            }
        
        # Contradiction Type 2: Free/0đ with buffet (impossible)
        has_free = any(word in query_lower for word in ['0d', '0 d', 'mien phi', 'free', 'khong mat tien', 'khong ton tien'])
        
        if has_free and 'buffet' in query_lower:
            if language == "vi":
                message = (
                    "Ủa, **buffet 0đ** hay **miễn phí** à? 😳\n\n"
                    "Mình nghĩ bạn nhầm rồi đó! Không có quán buffet nào miễn phí cả bạn ơi 😅\n\n"
                    "Có lẽ bạn muốn:\n"
                    "1️⃣ **Buffet giá rẻ** (dưới 200k)?\n"
                    "2️⃣ **Quán có khuyến mãi** hoặc voucher giảm giá?\n"
                    "3️⃣ Hay **buffet bình dân**, giá sinh viên?\n\n"
                    "Nói rõ cho mình biết nhé! 😊"
                )
            else:
                message = (
                    "Wait, **free buffet** or **0đ**? 😳\n\n"
                    "I think you're mistaken! There's no such thing as free buffet 😅\n\n"
                    "Maybe you want:\n"
                    "1️⃣ **Cheap buffet** (under 200k)?\n"
                    "2️⃣ Places with **promotions** or discount vouchers?\n"
                    "3️⃣ Or **affordable buffet**, student prices?\n\n"
                    "Let me know! 😊"
                )
            
            return {
                "message": message,
                "restaurants": [],
                "language": language,
                "needs_clarification": True
            }
        
        # No contradiction detected - let RAG handle the query normally
        return None
    
    def _generate_greeting_response(self, language: str) -> Dict[str, Any]:
        """Generate friendly greeting response."""
        if language == "vi":
            message = (
                "Xin chào! 👋\n\n"
                "Mình là trợ lý AI chuyên tư vấn món ăn và nhà hàng tại TP.HCM.\n\n"
                "Mình có thể giúp bạn:\n"
                "🍜 Tìm quán ăn theo món (phở, cơm, bún, lẩu, hải sản...)\n"
                "📍 Tìm quán gần bạn hoặc theo quận\n"
                "💰 Lọc theo giá cả phù hợp túi tiền\n"
                "⭐ Gợi ý quán ngon, rating cao\n\n"
                "Bạn muốn ăn gì hôm nay? Cứ hỏi mình nhé! 😊"
            )
        else:
            message = (
                "Hello! 👋\n\n"
                "I'm your AI assistant for food and restaurant recommendations in Ho Chi Minh City.\n\n"
                "I can help you:\n"
                "🍜 Find restaurants by cuisine (pho, rice, noodles, hotpot, seafood...)\n"
                "📍 Search nearby or by district\n"
                "💰 Filter by price range\n"
                "⭐ Suggest top-rated restaurants\n\n"
                "What would you like to eat today? Just ask me! 😊"
            )
        
        return {
            "message": message,
            "restaurants": [],
            "restaurant_count": 0,
            "language": language,
            "is_greeting": True
        }
    
    def _generate_off_topic_response(self, language: str) -> Dict[str, Any]:
        """Generate friendly response for off-topic queries (hospitals, tourism, etc)."""
        if language == "vi":
            message = (
                "Xin lỗi bạn nhé! 😊\n\n"
                "Tôi là AI chuyên tư vấn về món ăn và nhà hàng thôi. "
                "Những câu hỏi về bệnh viện, du lịch, shopping hay các dịch vụ khác thì tôi không giỏi lắm. 🍜\n\n"
                "Nhưng nếu bạn đang đói hoặc muốn tìm quán ăn ngon, hãy hỏi tôi nhé!\n"
                "Ví dụ: 'Tìm quán phở gần Quận 1' hoặc 'Gợi ý quán hải sản giá rẻ' là được nha. 😄"
            )
        else:
            message = (
                "Sorry! 😊\n\n"
                "I specialize in food and restaurant recommendations only. "
                "Questions about hospitals, tourism, shopping, or other services are outside my expertise. 🍜\n\n"
                "But if you're hungry or looking for good places to eat, feel free to ask me!\n"
                "For example: 'Find pho restaurant near District 1' or 'Suggest affordable seafood restaurant'. 😄"
            )
        
        return {
            "message": message,
            "restaurants": [],
            "restaurant_count": 0,
            "language": language,
            "is_off_topic": True
        }
    
    async def _generate_no_results_response(
        self,
        query: str,
        language: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response when no restaurants match."""
        # Check if location sharing is needed
        if params.get('needs_location_warning'):
            if language == 'vi':
                return {
                    "message": "⚠️ Để tìm quán gần bạn, vui lòng chia sẻ vị trí của bạn!\n\nHoặc bạn có thể chỉ rõ quận (ví dụ: 'tìm quán gần quận 1').",
                    "restaurants": [],
                    "restaurant_count": 0,
                    "language": language,
                    "params": params
                }
            else:
                return {
                    "message": "⚠️ To find restaurants near you, please share your location!\n\nOr you can specify a district (e.g., 'find restaurant near District 1').",
                    "restaurants": [],
                    "restaurant_count": 0,
                    "language": language,
                    "params": params
                }
        
        # Build specific suggestions based on params
        suggestions = []
        
        # Don't suggest budget changes - confusing for users
        
        # Suggest expanding distance if query mentions distance
        if params.get('max_distance'):
            distance = params['max_distance']
            if language == 'vi':
                suggestions.append(f"Mở rộng bán kính tìm kiếm (hiện tại: {distance}km)?")
            else:
                suggestions.append(f"Expand search radius (current: {distance}km)?")
        
        # Suggest expanding location area
        if params.get('locations'):
            if language == 'vi':
                suggestions.append(f"Mở rộng khu vực tìm kiếm sang quận lân cận?")
            else:
                suggestions.append(f"Expand search area to nearby districts?")
        
        if language == 'vi':
            message = f"Xin lỗi, tôi không tìm thấy nhà hàng phù hợp.\n\n"
            if suggestions:
                message += "Gợi ý:\n" + "\n".join(f"- {s}" for s in suggestions)
            else:
                message += "Bạn có thể thử:\n"
                message += "- Tìm kiếm với từ khóa khác (ví dụ: 'quán phở quận 1')\n"
                message += "- Chỉ rõ khu vực hoặc loại món ăn bạn muốn"
        else:
            message = f"Sorry, I couldn't find any restaurants matching your request.\n\n"
            if suggestions:
                message += "Would you like to:\n" + "\n".join(f"- {s}" for s in suggestions)
            else:
                message += "Suggestions:\n"
                message += "- Try different search keywords\n"
                message += "- Provide more details about area or cuisine type\n"
                message += "- Broaden your search criteria"
        
        return {
            "message": message,
            "restaurants": [],
            "restaurant_count": 0,
            "language": language,
            "params": params
        }
    
    async def _generate_response_with_results(
        self,
        query: str,
        restaurants: List[Dict[str, Any]],
        language: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response with restaurant recommendations."""
        # Add location warning if needed
        location_note = ""
        if params.get('needs_location_warning'):
            if language == 'vi':
                location_note = "\n\nℹ️ Lưu ý: Kết quả chưa được sắp xếp theo khoảng cách. Vui lòng chia sẻ vị trí để tìm quán gần bạn nhất!"
            else:
                location_note = "\n\nℹ️ Note: Results are not sorted by distance. Please share your location to find nearest restaurants!"
        
        system_prompt = self._get_system_prompt(language)
        
        # Prepare restaurant context
        restaurant_context = self._format_restaurant_context(restaurants, language)
        
        # Check budget constraints
        budget_note = ""
        if params.get('max_budget'):
            max_budget = params['max_budget']
            over_budget = [r for r in restaurants if self._estimate_price(r) > max_budget]
            if over_budget:
                budget_note = f"\n\n(Lưu ý: Một số nhà hàng có thể vượt ngân sách {max_budget:,}đ của bạn)"
        
        # Add atmosphere/context note for LLM
        atmosphere_note = ""
        if params.get('atmosphere'):
            atmo = params['atmosphere']
            if 'romantic' in atmo:
                atmosphere_note = "\n- Người dùng muốn không gian lãng mạn, thích hợp hẹn hò → ưu tiên nhà hàng có view đẹp, không gian sang trọng"
            elif 'quick' in atmo:
                atmosphere_note = "\n- Người dùng cần nhanh/gấp → ưu tiên nhà hàng gần, phục vụ nhanh"
            elif 'luxury' in atmo:
                atmosphere_note = "\n- Người dùng muốn sang trọng, cao cấp → ưu tiên nhà hàng có rating cao, không gian đẹp"
            elif 'family' in atmo:
                atmosphere_note = "\n- Người dùng đi gia đình → ưu tiên nhà hàng rộng rãi, phục vụ đa dạng"
        
        prompt = f"""
Người dùng hỏi: "{query}"

Thông tin các nhà hàng phù hợp:
{restaurant_context}

Yêu cầu:
1. Giới thiệu {'bằng tiếng Việt' if language == 'vi' else 'in English'}, tự nhiên và thân thiện
2. CHỈ giới thiệu {len(restaurants)} nhà hàng có trong danh sách (KHÔNG làm tròn lên 5)
3. Giải thích ngắn gọn lý do đề xuất mỗi nhà hàng dựa trên thông tin có sẵn
4. Sắp xếp theo độ phù hợp với yêu cầu{atmosphere_note}
5. Cuối cùng, hỏi người dùng có cần thông tin chi tiết hơn không{budget_note}

⚠️ QUAN TRỌNG - CHỐNG HALLUCINATION:
- TUYỆT ĐỐI KHÔNG tự tưởng tượng thông tin không có
- TUYỆT ĐỐI KHÔNG bịa thêm nhà hàng ngoài danh sách
- CHỉ dùng đúng {len(restaurants)} nhà hàng đã cung cấp
- Nếu thiếu thông tin, nói rõ "chưa có thông tin" hoặc bỏ qua
- Nếu danh sách có ít hơn 5 quán thì CHỈ giới thiệu đúng số đó
"""
        
        message = await ollama_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        # Add location note if needed with proper formatting
        if location_note:
            message = message.strip() + "\n\n" + location_note
        else:
            message = message
        
        # Prepare restaurant list for response (return up to 10)
        restaurant_list = []
        for r in restaurants[:10]:
            restaurant_list.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "address": r.get("address"),
                "phone": r.get("phone"),
                "website": r.get("website"),
                "rating": r.get("rating"),
                "rating_count": r.get("rating_count"),
                "price_level": r.get("price_level"),
                "food_tags": r.get("food_tags", []),
                "coordinates_lat": r.get("coordinates_lat"),
                "coordinates_lon": r.get("coordinates_lon"),
                "distance": r.get("distance"),
                "distance_text": r.get("distance_text"),
                "relevance_score": r.get("relevance_score"),
                # NEW advanced features
                "trending_score": r.get("trending_score"),
                "is_open": r.get("is_open"),
                "open_status": r.get("open_status"),
                "badges": r.get("badges"),
                "signature_dishes": r.get("signature_dishes"),
                "review_insights": r.get("review_insights")
            })
        
        return {
            "message": message,
            "restaurants": restaurant_list,
            "restaurant_count": len(restaurant_list),
            "language": language,
            "params": params,
            "explanation": "Recommendations based on your query, location, and preferences"
        }
    
    def _format_restaurant_context(
        self,
        restaurants: List[Dict[str, Any]],
        language: str
    ) -> str:
        """Format restaurant data for LLM context."""
        context_parts = []
        
        for i, r in enumerate(restaurants[:10], 1):
            parts = [f"#{i}. {r.get('name', 'N/A')}"]
            
            if r.get('address'):
                parts.append(f"   Địa chỉ: {r['address']}")
            
            if r.get('rating'):
                parts.append(f"   Rating: {r['rating']}/5 ({r.get('rating_count', 0)} đánh giá)")
            
            if r.get('price_level'):
                price_text = self._price_level_to_text(r['price_level'], language)
                parts.append(f"   Giá: {price_text}")
            
            if r.get('food_tags'):
                tags = ", ".join(r['food_tags'][:5])
                parts.append(f"   Món: {tags}")
            
            if r.get('distance') is not None:
                parts.append(f"   Khoảng cách: {r['distance']}km")
            
            if r.get('phone'):
                parts.append(f"   SĐT: {r['phone']}")
            
            context_parts.append("\n".join(parts))
        
        return "\n\n".join(context_parts)
    
    def _price_level_to_text(self, price_level: str, language: str) -> str:
        """Convert price level to readable text."""
        mappings = {
            "vi": {
                "PRICE_LEVEL_INEXPENSIVE": "Bình dân (< 100k/người)",
                "PRICE_LEVEL_MODERATE": "Trung bình (100-200k/người)",
                "PRICE_LEVEL_EXPENSIVE": "Cao cấp (200-500k/người)",
                "PRICE_LEVEL_VERY_EXPENSIVE": "Sang trọng (> 500k/người)"
            },
            "en": {
                "PRICE_LEVEL_INEXPENSIVE": "Budget-friendly (< 100k/person)",
                "PRICE_LEVEL_MODERATE": "Moderate (100-200k/person)",
                "PRICE_LEVEL_EXPENSIVE": "Upscale (200-500k/person)",
                "PRICE_LEVEL_VERY_EXPENSIVE": "Fine dining (> 500k/person)"
            }
        }
        
        return mappings.get(language, mappings["vi"]).get(
            price_level,
            price_level
        )
    
    def _estimate_price(self, restaurant: Dict[str, Any]) -> float:
        """Estimate average price per person."""
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': 75000,
            'PRICE_LEVEL_MODERATE': 150000,
            'PRICE_LEVEL_EXPENSIVE': 350000,
            'PRICE_LEVEL_VERY_EXPENSIVE': 600000
        }
        return price_map.get(restaurant.get('price_level', ''), 150000)
    
    def _enrich_restaurant_data(
        self,
        restaurants: List[Dict[str, Any]],
        user_location: Optional[Dict[str, float]] = None,
        language: str = "vi",
        group_size: Optional[int] = None,
        filter_open: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Enrich restaurant data with advanced features:
        - Opening status & time-aware filtering
        - Distance calculation
        - Trending scores
        - Badges
        - Review insights
        - Signature dishes
        - Group suitability
        
        Args:
            restaurants: List of restaurant dictionaries
            user_location: User's location {lat, lon}
            language: Language for formatting
            group_size: Number of people in group
            filter_open: Whether to filter out closed restaurants
            
        Returns:
            Enriched and optionally filtered restaurant list
        """
        from utils import (
            is_restaurant_open, calculate_distance, format_distance,
            calculate_trending_score, get_restaurant_badges,
            analyze_review_sentiment, extract_signature_dishes,
            format_review_insights, is_group_friendly
        )
        
        enriched = []
        
        for restaurant in restaurants:
            # Defensive check: ensure restaurant is a dictionary
            if not isinstance(restaurant, dict):
                continue
            
            # 1. Check opening status
            opening_hours = restaurant.get('opening_hours', {})
            is_open, status_msg = is_restaurant_open(opening_hours)
            restaurant['is_open'] = is_open
            restaurant['open_status'] = status_msg
            
            # Filter out closed restaurants if requested
            if filter_open and not is_open:
                continue
            
            # 2. Calculate distance if user location provided
            if user_location and 'lat' in user_location and 'lon' in user_location:
                rest_lat = restaurant.get('coordinates_lat')
                rest_lon = restaurant.get('coordinates_lon')
                if rest_lat is not None and rest_lon is not None:
                    distance = calculate_distance(
                        user_location['lat'], user_location['lon'],
                        rest_lat, rest_lon
                    )
                    restaurant['distance'] = distance
                    restaurant['distance_text'] = format_distance(distance, language)
                else:
                    restaurant['distance'] = None
                    restaurant['distance_text'] = None
            else:
                restaurant['distance'] = None
                restaurant['distance_text'] = None
            
            # 3. Calculate trending score
            rating = restaurant.get('rating', 0)
            rating_count = restaurant.get('rating_count', 0)
            trending_score = calculate_trending_score(rating, rating_count)
            restaurant['trending_score'] = trending_score
            
            # 4. Generate badges
            badges = get_restaurant_badges(
                rating=rating,
                rating_count=rating_count,
                trending_score=trending_score,
                is_open=is_open,
                distance=restaurant.get('distance')
            )
            
            # 5. Check group suitability if group_size provided
            if group_size and group_size >= 4:
                is_suitable, reasons = is_group_friendly(restaurant, group_size)
                if is_suitable:
                    badges.append(f"👥 PHÙ HỢP NHÓM {group_size} NGƯỜI")
                    restaurant['group_suitability'] = reasons
            
            restaurant['badges'] = badges
            
            # 6. Analyze reviews for insights
            comments = restaurant.get('comments', [])
            if comments:
                # Sentiment analysis
                insights = analyze_review_sentiment(comments)
                insights_text = format_review_insights(insights, language)
                restaurant['review_insights'] = insights_text
                
                # Extract signature dishes
                signature_dishes = extract_signature_dishes(comments, top_n=3)
                restaurant['signature_dishes'] = signature_dishes
            else:
                restaurant['review_insights'] = None
                restaurant['signature_dishes'] = []
            
            enriched.append(restaurant)
        
        return enriched
    
    def _rank_with_advanced_scoring(
        self,
        restaurants: List[Dict[str, Any]],
        params: Dict[str, Any],
        user_location: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Advanced ranking algorithm considering multiple factors:
        - Original relevance score (40%)
        - Trending score (25%)
        - Distance score (20% if location provided)
        - Opening status bonus (10%)
        - Group suitability bonus (5%)
        
        Args:
            restaurants: List of enriched restaurants
            params: Search parameters
            user_location: User's location
            
        Returns:
            Sorted list of restaurants
        """
        for restaurant in restaurants:
            final_score = 0.0
            
            # 1. Relevance score (40%)
            relevance = restaurant.get('relevance_score', 0.5)
            final_score += relevance * 0.4
            
            # 2. Trending score (25%)
            trending = restaurant.get('trending_score', 5.0) / 10.0  # Normalize to 0-1
            final_score += trending * 0.25
            
            # 3. Distance score (20% if applicable)
            if user_location and restaurant.get('distance') is not None:
                distance = restaurant['distance']
                # Closer is better: score decreases with distance
                # 0km = 1.0, 5km = 0.5, 10km+ = 0.0
                distance_score = max(0, 1 - (distance / 10.0))
                final_score += distance_score * 0.20
            else:
                # If no location, redistribute weight to other factors
                final_score += relevance * 0.10
                final_score += trending * 0.10
            
            # 4. Opening status bonus (10%)
            if restaurant.get('is_open', True):
                final_score += 0.10
            
            # 5. Group suitability bonus (5%)
            if params.get('group_size') and restaurant.get('group_suitability'):
                final_score += 0.05
            
            restaurant['final_score'] = round(final_score, 4)
        
        # Sort by final score
        restaurants.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return restaurants
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt for LLM."""
        if language == "vi":
            return """Bạn là trợ lý AI chuyên về ẩm thực và nhà hàng tại TP.HCM.
            
Nhiệm vụ:
- Giới thiệu nhà hàng/món ăn phù hợp với yêu cầu người dùng
- Giải thích rõ ràng lý do đề xuất
- Cung cấp thông tin chính xác từ database
- KHÔNG tự tưởng tượng hoặc bịa đặt thông tin
- Thân thiện, nhiệt tình nhưng chuyên nghiệp
- Luôn hỏi feedback để cải thiện

Nguyên tắc:
- Chỉ dùng thông tin có trong dữ liệu đã cung cấp
- Nếu không chắc chắn, nói rõ "chưa có thông tin"
- Minh bạch về giá cả và khoảng cách
- Tôn trọng ngân sách và sở thích người dùng"""
        else:
            return """You are an AI assistant specializing in food and restaurants in Ho Chi Minh City.

Your tasks:
- Recommend restaurants/dishes based on user requirements
- Explain clearly why you recommend each option
- Provide accurate information from the database
- DO NOT imagine or fabricate information
- Be friendly and enthusiastic but professional
- Always ask for feedback to improve

Principles:
- Only use information provided in the data
- If unsure, clearly state "information not available"
- Be transparent about pricing and distance
- Respect user budget and preferences"""


# Global instance
rag_pipeline = RAGPipeline()
