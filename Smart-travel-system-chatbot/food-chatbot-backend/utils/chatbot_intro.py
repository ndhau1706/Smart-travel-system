"""
Chatbot Introduction Helper
Provides introduction messages when user asks off-topic questions.
"""
from typing import Optional


def get_chatbot_introduction(language: str = 'vi', user_name: Optional[str] = None) -> str:
    """
    Get chatbot introduction message for off-topic queries.
    
    Args:
        language: 'vi' or 'en'
        user_name: Optional user name for personalization
        
    Returns:
        Introduction message
    """
    greeting = f"Xin chào {user_name}! " if user_name else "👋 Xin chào! "
    
    if language == 'vi':
        return (
            f"{greeting}Tôi là **AI Tư vấn Ẩm thực TP.HCM** 🍜\n\n"
            "**🎯 Tôi có thể giúp bạn**:\n"
            "• Tìm quán ăn theo sở thích\n"
            "• Gợi ý món ăn phù hợp\n"
            "• Tìm nhà hàng gần bạn\n"
            "• So sánh giá cả, rating\n"
            "• Xem review khách hàng\n"
            "• Kiểm tra giờ mở cửa\n\n"
            "**💬 Ví dụ câu hỏi**:\n"
            "• \"Tìm quán phở ngon quận 1\"\n"
            "• \"Nhà hàng hải sản giá rẻ\"\n"
            "• \"Quán cafe view đẹp\"\n"
            "• \"Buffet gần tôi\"\n"
            "• \"So sánh 2 quán đầu\"\n\n"
            "**❓ Bạn muốn tìm quán gì hôm nay?**"
        )
    else:  # English
        greeting_en = f"Hello {user_name}! " if user_name else "👋 Hello! "
        return (
            f"{greeting_en}I'm your **AI Food Advisor for Ho Chi Minh City** 🍜\n\n"
            "**🎯 I can help you**:\n"
            "• Find restaurants by preferences\n"
            "• Suggest suitable dishes\n"
            "• Find nearby restaurants\n"
            "• Compare prices & ratings\n"
            "• Check customer reviews\n"
            "• Verify opening hours\n\n"
            "**💬 Example queries**:\n"
            "• \"Find good pho in District 1\"\n"
            "• \"Cheap seafood restaurant\"\n"
            "• \"Cafe with nice view\"\n"
            "• \"Buffet near me\"\n"
            "• \"Compare first 2 restaurants\"\n\n"
            "**❓ What would you like to eat today?**"
        )


def get_off_topic_response(query: str, language: str = 'vi') -> str:
    """
    Get response for off-topic questions.
    
    Detects common off-topic patterns and returns friendly redirect.
    
    Args:
        query: User query
        language: 'vi' or 'en'
        
    Returns:
        Off-topic response
    """
    query_lower = query.lower()
    
    # Detect specific off-topic categories
    if any(word in query_lower for word in ['thời tiết', 'weather', 'nhiệt độ', 'temperature']):
        if language == 'vi':
            return (
                "😊 Tôi là chuyên gia về ẩm thực, không phải thời tiết nhé!\n\n"
                "Nhưng nếu bạn muốn tìm quán phù hợp với thời tiết hôm nay:\n"
                "• Trời nắng → Quán cafe có điều hòa, quán nước mát\n"
                "• Trời mưa → Nhà hàng trong nhà, quán lẩu\n"
                "• Trời lạnh → Quán phở, bún, lẩu\n\n"
                "Bạn muốn tìm loại quán nào?"
            )
        else:
            return (
                "😊 I'm a food expert, not a weather forecaster!\n\n"
                "But if you want restaurants suitable for today's weather:\n"
                "• Sunny → Air-conditioned cafes, cold drinks\n"
                "• Rainy → Indoor restaurants, hotpot\n"
                "• Cold → Pho, noodles, hotpot\n\n"
                "What type of restaurant are you looking for?"
            )
    
    elif any(word in query_lower for word in ['tin tức', 'news', 'bóng đá', 'football', 'soccer']):
        if language == 'vi':
            return (
                "⚽ Tôi không theo dõi tin tức/thể thao, nhưng...\n\n"
                "Nếu bạn muốn xem bóng đá và ăn uống:\n"
                "• Quán có TV lớn\n"
                "• Quán nhậu, beer club\n"
                "• Nhà hàng có không gian ngoài trời\n\n"
                "Tôi có thể gợi ý quán xem bóng đá không?"
            )
        else:
            return (
                "⚽ I don't follow news/sports, but...\n\n"
                "If you want to watch football and eat:\n"
                "• Restaurants with big TV screens\n"
                "• Beer clubs, sports bars\n"
                "• Outdoor dining spaces\n\n"
                "Shall I suggest sports viewing restaurants?"
            )
    
    # Generic off-topic
    return get_chatbot_introduction(language)


# Friendly error messages for different scenarios
def get_no_results_message(language: str = 'vi') -> str:
    """Get message when no restaurants match criteria"""
    if language == 'vi':
        return (
            "😔 Không tìm thấy quán phù hợp với yêu cầu của bạn.\n\n"
            "**Gợi ý**:\n"
            "• Thử mở rộng khu vực tìm kiếm\n"
            "• Điều chỉnh ngân sách\n"
            "• Thay đổi loại món ăn\n"
            "• Hỏi tổng quát hơn\n\n"
            "Bạn muốn tôi gợi ý quán tương tự không?"
        )
    else:
        return (
            "😔 No restaurants match your criteria.\n\n"
            "**Suggestions**:\n"
            "• Expand search area\n"
            "• Adjust budget\n"
            "• Try different cuisine\n"
            "• Ask more generally\n\n"
            "Would you like similar recommendations?"
        )


def get_need_more_info_message(language: str = 'vi', missing_params: list = None) -> str:
    """Get message when more information is needed"""
    if language == 'vi':
        base = "🤔 Tôi cần thêm thông tin để gợi ý chính xác hơn.\n\n"
        if missing_params:
            base += "**Thiếu**:\n"
            param_names = {
                'cuisine': 'Loại món ăn (phở, lẩu, hải sản...)',
                'location': 'Khu vực (quận 1, quận 3...)',
                'price': 'Ngân sách (rẻ, trung bình, cao cấp)',
                'atmosphere': 'Không gian (yên tĩnh, náo nhiệt...)'
            }
            for param in missing_params:
                base += f"• {param_names.get(param, param)}\n"
        base += "\nBạn có thể cho tôi biết thêm không?"
        return base
    else:
        base = "🤔 I need more information for better suggestions.\n\n"
        if missing_params:
            base += "**Missing**:\n"
            param_names = {
                'cuisine': 'Cuisine type (pho, hotpot, seafood...)',
                'location': 'Area (District 1, District 3...)',
                'price': 'Budget (cheap, moderate, expensive)',
                'atmosphere': 'Atmosphere (quiet, lively...)'
            }
            for param in missing_params:
                base += f"• {param_names.get(param, param)}\n"
        base += "\nCan you provide more details?"
        return base
