"""
Rich Response Formatter
Creates visually appealing, structured responses
"""
from typing import Dict, List, Optional, Any
import re


class ResponseFormatter:
    """Format responses with rich visual structure."""
    
    def __init__(self):
        self.emojis = {
            'cuisine': {
                'vietnamese': '🇻🇳',
                'japanese': '🇯🇵',
                'korean': '🇰🇷',
                'chinese': '🇨🇳',
                'thai': '🇹🇭',
                'italian': '🇮🇹',
                'french': '🇫🇷',
                'american': '🇺🇸',
                'indian': '🇮🇳',
                'mexican': '🇲🇽',
                'default': '🍽️'
            },
            'attributes': {
                'rating': '⭐',
                'price': '💰',
                'location': '📍',
                'distance': '🚶',
                'open': '🟢',
                'closed': '🔴',
                'phone': '📞',
                'parking': '🅿️',
                'wifi': '📶',
                'card': '💳',
                'delivery': '🚚',
                'booking': '📅',
                'vegetarian': '🥗',
                'halal': '☪️'
            },
            'actions': {
                'search': '🔍',
                'recommend': '💡',
                'error': '❌',
                'success': '✅',
                'warning': '⚠️',
                'info': 'ℹ️',
                'question': '❓'
            }
        }
    
    def format_restaurant_card(
        self,
        restaurant: Dict[str, Any],
        show_explanation: bool = False,
        rank: Optional[int] = None
    ) -> str:
        """
        Format single restaurant as a card.
        
        Args:
            restaurant: Restaurant data
            show_explanation: Include recommendation explanation
            rank: Restaurant rank in results
            
        Returns:
            Formatted card
        """
        lines = []
        
        # Header with rank and name
        header = "━━━━━━━━━━━━━━━━━━━━━\n"
        if rank:
            header += f"**#{rank}** "
        header += f"**{restaurant.get('name', 'Unknown')}**"
        lines.append(header)
        
        # Cuisine with flag
        cuisine = restaurant.get('cuisine', 'Unknown')
        cuisine_emoji = self._get_cuisine_emoji(cuisine)
        lines.append(f"{cuisine_emoji} {cuisine.title()}")
        
        # Rating
        rating = restaurant.get('rating', 0)
        rating_str = self._format_rating(rating)
        lines.append(f"{self.emojis['attributes']['rating']} {rating_str}")
        
        # Price level
        price_level = restaurant.get('price_level', '')
        price_str = self._format_price_level(price_level)
        price_vnd = self._format_price_vnd(price_level)  # Thêm giá VNĐ
        lines.append(f"{self.emojis['attributes']['price']} {price_str} ({price_vnd})")
        
        # Location
        location = restaurant.get('location', 'Unknown')
        lines.append(f"{self.emojis['attributes']['location']} {location}")
        
        # Distance
        distance = restaurant.get('distance')
        if distance:
            lines.append(f"{self.emojis['attributes']['distance']} {distance:.1f} km")
        
        # Opening status
        is_open = restaurant.get('is_open_now', True)
        status_emoji = self.emojis['attributes']['open'] if is_open else self.emojis['attributes']['closed']
        status_text = "Đang mở cửa" if is_open else "Đã đóng cửa"
        lines.append(f"{status_emoji} {status_text}")
        
        # Phone
        phone = restaurant.get('phone')
        if phone:
            lines.append(f"{self.emojis['attributes']['phone']} {phone}")
        
        # Additional features (parking, wifi, card, delivery)
        features = []
        if restaurant.get('has_parking'):
            features.append(f"{self.emojis['attributes']['parking']} Bãi đậu xe")
        if restaurant.get('has_wifi'):
            features.append(f"{self.emojis['attributes']['wifi']} WiFi")
        if restaurant.get('accepts_card'):
            features.append(f"{self.emojis['attributes']['card']} Thẻ")
        if restaurant.get('has_delivery'):
            features.append(f"{self.emojis['attributes']['delivery']} Giao hàng")
        
        if features:
            lines.append(" • ".join(features))
        
        # Explanation if requested
        if show_explanation and restaurant.get('explanation'):
            lines.append(f"\n💡 **Lý do gợi ý:** {restaurant['explanation']}")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━\n")
        
        return "\n".join(lines)
    
    def format_restaurant_list(
        self,
        restaurants: List[Dict[str, Any]],
        show_explanations: bool = False,
        max_display: int = 5
    ) -> str:
        """
        Format list of restaurants.
        
        Args:
            restaurants: List of restaurants
            show_explanations: Include explanations
            max_display: Maximum restaurants to display
            
        Returns:
            Formatted list
        """
        if not restaurants:
            return f"{self.emojis['actions']['error']} Không tìm thấy nhà hàng phù hợp."
        
        result_parts = []
        
        # Header
        total = len(restaurants)
        display_count = min(max_display, total)
        header = f"{self.emojis['actions']['search']} **Tìm thấy {total} nhà hàng**"
        if total > max_display:
            header += f" (hiển thị {display_count} quán đầu tiên)"
        result_parts.append(header + "\n")
        
        # Format each restaurant
        for idx, restaurant in enumerate(restaurants[:max_display], 1):
            card = self.format_restaurant_card(
                restaurant,
                show_explanation=show_explanations,
                rank=idx
            )
            result_parts.append(card)
        
        return "\n".join(result_parts)
    
    def format_comparison_table(
        self,
        restaurants: List[Dict[str, Any]],
        attributes: List[str] = None
    ) -> str:
        """
        Format restaurants as comparison table.
        
        Args:
            restaurants: List of restaurants to compare
            attributes: Attributes to compare
            
        Returns:
            Formatted table
        """
        if not restaurants:
            return "Không có nhà hàng để so sánh."
        
        if attributes is None:
            attributes = ['name', 'rating', 'price_level', 'distance', 'cuisine']
        
        # Build header
        lines = ["**So sánh nhà hàng**\n"]
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Build table
        for restaurant in restaurants:
            lines.append(f"\n**{restaurant.get('name', 'Unknown')}**")
            
            if 'rating' in attributes:
                rating = self._format_rating(restaurant.get('rating', 0))
                lines.append(f"  {self.emojis['attributes']['rating']} Rating: {rating}")
            
            if 'price_level' in attributes:
                price = self._format_price_level(restaurant.get('price_level', ''))
                lines.append(f"  {self.emojis['attributes']['price']} Giá: {price}")
            
            if 'distance' in attributes and restaurant.get('distance'):
                lines.append(f"  {self.emojis['attributes']['distance']} Khoảng cách: {restaurant['distance']:.1f} km")
            
            if 'cuisine' in attributes:
                cuisine = restaurant.get('cuisine', 'Unknown')
                emoji = self._get_cuisine_emoji(cuisine)
                lines.append(f"  {emoji} Món: {cuisine.title()}")
            
            if 'location' in attributes:
                lines.append(f"  {self.emojis['attributes']['location']} Địa chỉ: {restaurant.get('location', 'N/A')}")
        
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    def format_clarification_question(
        self,
        question: str,
        options: List[str],
        context: Optional[str] = None
    ) -> str:
        """
        Format clarification question with options.
        
        Args:
            question: Question text
            options: List of options
            context: Optional context
            
        Returns:
            Formatted question
        """
        lines = []
        
        # Context if provided
        if context:
            lines.append(f"{self.emojis['actions']['info']} {context}\n")
        
        # Question
        lines.append(f"{self.emojis['actions']['question']} **{question}**\n")
        
        # Options
        for idx, option in enumerate(options, 1):
            lines.append(f"  {idx}. {option}")
        
        return "\n".join(lines)
    
    def format_error_message(
        self,
        error_type: str,
        message: str,
        suggestion: Optional[str] = None
    ) -> str:
        """
        Format error message.
        
        Args:
            error_type: Type of error
            message: Error message
            suggestion: Optional suggestion
            
        Returns:
            Formatted error
        """
        lines = []
        
        lines.append(f"{self.emojis['actions']['error']} **Lỗi: {error_type}**")
        lines.append(f"{message}")
        
        if suggestion:
            lines.append(f"\n{self.emojis['actions']['info']} Gợi ý: {suggestion}")
        
        return "\n".join(lines)
    
    def format_success_message(
        self,
        action: str,
        details: Optional[str] = None
    ) -> str:
        """
        Format success message.
        
        Args:
            action: Action completed
            details: Optional details
            
        Returns:
            Formatted message
        """
        message = f"{self.emojis['actions']['success']} {action}"
        if details:
            message += f"\n{details}"
        return message
    
    def enhance_response(self, response: str) -> str:
        """
        Enhance plain response with formatting.
        
        Args:
            response: Plain response
            
        Returns:
            Enhanced response
        """
        # Add emojis to key phrases
        enhancements = {
            r'\b(tìm thấy|found)\b': f"{self.emojis['actions']['search']} \\1",
            r'\b(gợi ý|recommend)\b': f"{self.emojis['actions']['recommend']} \\1",
            r'\b(đang mở|open now)\b': f"{self.emojis['attributes']['open']} \\1",
            r'\b(đã đóng|closed)\b': f"{self.emojis['attributes']['closed']} \\1",
            r'\b(rating|đánh giá)\b': f"{self.emojis['attributes']['rating']} \\1",
        }
        
        enhanced = response
        for pattern, replacement in enhancements.items():
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
        
        return enhanced
    
    def _get_cuisine_emoji(self, cuisine: str) -> str:
        """Get emoji for cuisine type."""
        cuisine_lower = cuisine.lower()
        return self.emojis['cuisine'].get(cuisine_lower, self.emojis['cuisine']['default'])
    
    def _format_rating(self, rating: float) -> str:
        """Format rating as stars."""
        if rating >= 4.5:
            return f"{rating:.1f} (Xuất sắc)"
        elif rating >= 4.0:
            return f"{rating:.1f} (Rất tốt)"
        elif rating >= 3.5:
            return f"{rating:.1f} (Tốt)"
        elif rating >= 3.0:
            return f"{rating:.1f} (Khá)"
        else:
            return f"{rating:.1f} (Trung bình)"
    
    def _format_price_level(self, price_level: str) -> str:
        """Format price level."""
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': '$ (Rẻ)',
            'PRICE_LEVEL_MODERATE': '$$ (Vừa phải)',
            'PRICE_LEVEL_EXPENSIVE': '$$$ (Đắt)',
            'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$ (Rất đắt)'
        }
        return price_map.get(price_level, '$$')
    
    def _format_price_vnd(self, price_level: str) -> str:
        """
        Format price level to Vietnamese Dong range.
        
        Maps PRICE_LEVEL to VNĐ:
        - INEXPENSIVE: 0-100,000đ (Giá rẻ)
        - MODERATE: 150,000-400,000đ (Trung bình)
        - EXPENSIVE: 400,000đ+ (Cao cấp)
        
        Args:
            price_level: PRICE_LEVEL string from data
            
        Returns:
            VNĐ range string
        """
        price_vnd_map = {
            'PRICE_LEVEL_INEXPENSIVE': '0-100k',
            'PRICE_LEVEL_MODERATE': '150-400k',
            'PRICE_LEVEL_EXPENSIVE': '400k+',
            'PRICE_LEVEL_VERY_EXPENSIVE': '500k+'
        }
        return price_vnd_map.get(price_level, '100-300k')


# Global instance
response_formatter = ResponseFormatter()
