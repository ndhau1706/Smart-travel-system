"""
Food synonyms and canonical mapping for Vietnamese and English.
"""

VIETNAMESE_FOOD_SYNONYMS = {
    # Phở variants
    "phở": ["pho", "phở bò", "phở gà", "phở tái", "phở chín"],
    "pho": ["phở", "phở bò", "phở gà"],
    
    # Bánh mì variants
    "bánh mì": ["banh mi", "bánh mỳ", "banh my", "bánh mì thịt", "bánh mì pate"],
    "banh mi": ["bánh mì", "bánh mỳ"],
    
    # Cơm variants
    "cơm": ["com", "cơm tấm", "cơm sườn", "cơm gà", "cơm chiên"],
    "com": ["cơm", "cơm tấm"],
    "cơm tấm": ["com tam", "cơm sườn", "cơm sườn bì chả"],
    
    # Bún variants
    "bún": ["bun", "bun cha", "bún bò", "bún chả", "bún riêu", "bún đậu"],
    "bun": ["bún", "bún bò", "bún chả"],
    "bun cha": ["bún chả", "bún cha"],
    "bún bò huế": ["bun bo hue", "bún bò"],
    "bún chả": ["bun cha"],
    "bún riêu": ["bun rieu"],
    
    # Lẩu variants
    "lẩu": ["lau", "lẩu thái", "lẩu hải sản", "lẩu gà", "lẩu bò"],
    "lau": ["lẩu", "hotpot"],
    "hotpot": ["lẩu", "lau"],
    
    # Bánh variants
    "bánh xèo": ["banh xeo", "bánh khoái"],
    "bánh cuốn": ["banh cuon"],
    "bánh tráng": ["banh trang", "bánh đa"],
    
    # Gỏi/Nộm variants
    "gỏi": ["goi", "nộm", "nom", "salad"],
    "nộm": ["nom", "gỏi"],
    
    # Hải sản
    "hải sản": ["hai san", "seafood", "đồ biển"],
    "seafood": ["hải sản", "hai san"],
    
    # Thịt variants
    "thịt": ["thit", "meat", "heo", "bò", "gà"],
    "heo": ["lợn", "lon", "pork"],
    "bò": ["bo", "beef"],
    "gà": ["ga", "chicken"],
    
    # Món nướng
    "nướng": ["nuong", "grilled", "bbq", "nướng xiên", "nướng than"],
    "bbq": ["nướng", "nuong", "barbecue"],
    
    # Chè variants
    "chè": ["che", "dessert", "tráng miệng"],
    
    # Cà phê
    "cà phê": ["ca phe", "coffee", "cafe", "cà  phê", "caphe"],
    "ca phe": ["cà phê", "coffee", "cafe"],
    "coffee": ["cà phê", "ca phe", "cafe"],
    "cafe": ["cà phê", "ca phe", "coffee"],
    
    # Trà
    "trà": ["tra", "tea", "trà sữa"],
    "tea": ["trà", "tra"],
    "trà sữa": ["tra sua", "milk tea"],
    
    # Món Âu
    "steak": ["bít tết", "bit tet"],
    "pasta": ["mì ý", "mi y"],
    "pizza": ["bánh pizza"],
    
    # Món Nhật
    "sushi": ["sushi nhật"],
    "ramen": ["mì ramen"],
    "sashimi": ["sashimi nhật"],
    
    # Món Hàn
    "kimchi": ["kim chi"],
    "bulgogi": ["thịt nướng hàn quốc"],
    "bibimbap": ["cơm trộn hàn quốc"],
    
    # Món Thái
    "tom yum": ["tôm yum", "lẩu thái"],
    "pad thai": ["mì xào thái"],
}

CUISINE_TYPES = {
    "vietnamese": ["việt nam", "viet nam", "vietnamese", "vn", "việt"],
    "japanese": ["nhật", "nhật bản", "japan", "japanese"],
    "korean": ["hàn", "hàn quốc", "korea", "korean"],
    "thai": ["thái", "thái lan", "thailand", "thai"],
    "chinese": ["trung", "trung quốc", "china", "chinese"],
    "western": ["âu", "tây", "western", "europe", "european"],
    "italian": ["ý", "italy", "italian"],
    "french": ["pháp", "france", "french"],
}

ATMOSPHERE_KEYWORDS = {
    "chill": ["thoải mái", "thư giãn", "relax", "yên tĩnh", "quiet"],
    "cozy": ["ấm cúng", "cozy", "warm", "intimate"],
    "romantic": ["lãng mạn", "romantic", "couple", "date", "hẹn hò", "người yêu", 
                 "thơ mộng", "cảnh đẹp", "view đẹp", "lãng mạn", "tình cảm"],
    "luxury": ["sang trọng", "cao cấp", "luxury", "high-end", "fine dining"],
    "casual": ["bình dân", "giản dị", "casual", "simple"],
    "crowded": ["đông đúc", "sôi động", "lively", "busy"],
    "view": ["view đẹp", "scenic", "rooftop", "tầng cao", "cảnh đẹp"],
    "family": ["gia đình", "family", "trẻ em", "kids", "children"],
    "quick": ["nhanh", "gần", "quick", "fast", "đói", "hungry", "gấp"],
}

PRICE_KEYWORDS = {
    "cheap": ["rẻ", "bình dân", "giá rẻ", "cheap", "affordable", "budget"],
    "moderate": ["trung bình", "vừa phải", "moderate", "reasonable"],
    "expensive": ["đắt", "cao cấp", "expensive", "pricey", "high-end"],
}
