"""
Food synonyms and canonical mapping for Vietnamese and English.
"""

VIETNAMESE_FOOD_SYNONYMS = {
    # Phở variants
    "phở": ["pho", "phở bò", "phở gà", "phở tái", "phở chín", "phở nam định", "phở hà nội"],
    "pho": ["phở", "phở bò", "phở gà"],
    
    # Bánh mì variants
    "bánh mì": ["banh mi", "bánh mỳ", "banh my", "bánh mì thịt", "bánh mì pate", "bánh mì xíu mại", "bánh mì ốp la"],
    "banh mi": ["bánh mì", "bánh mỳ"],
    
    # Cơm variants
    "cơm": ["com", "cơm tấm", "cơm sườn", "cơm gà", "cơm chiên", "cơm rang", "cơm niêu"],
    "com": ["cơm", "cơm tấm"],
    "cơm tấm": ["com tam", "cơm sườn", "cơm sườn bì chả", "cơm tấm sài gòn"],
    "cơm chiên": ["com chien", "fried rice", "cơm rang"],
    
    # Bún variants
    "bún": ["bun", "bun cha", "bún bò", "bún chả", "bún riêu", "bún đậu", "bún mắm", "bún thịt nướng"],
    "bun": ["bún", "bún bò", "bún chả"],
    "bun cha": ["bún chả", "bún cha"],
    "bún bò huế": ["bun bo hue", "bún bò", "bún bò huế cay"],
    "bún chả": ["bun cha", "bún chả hà nội"],
    "bún riêu": ["bun rieu", "bún riêu cua"],
    "bún thịt nướng": ["bun thit nuong", "bún nem nướng"],
    
    # Hủ tiếu
    "hủ tiếu": ["hu tieu", "hủ tiếu nam vang", "hủ tiếu mỹ tho", "hủ tiếu khô"],
    "hu tieu": ["hủ tiếu"],
    
    # Mì variants
    "mì": ["mi", "mì quảng", "mì vằn thắn", "mì xào", "noodles"],
    "mi": ["mì", "noodles"],
    "mì quảng": ["mi quang"],
    
    # Lẩu variants
    "lẩu": ["lau", "lẩu thái", "lẩu hải sản", "lẩu gà", "lẩu bò", "lẩu nấm", "lẩu dê"],
    "lau": ["lẩu", "hotpot"],
    "hotpot": ["lẩu", "lau"],
    "lẩu thái": ["lau thai", "lẩu tom yum"],
    
    # Bánh variants
    "bánh xèo": ["banh xeo", "bánh khoái", "bánh xèo miền tây"],
    "bánh cuốn": ["banh cuon", "bánh cuốn thanh trì"],
    "bánh tráng": ["banh trang", "bánh đa", "bánh tráng trộn"],
    "bánh bao": ["banh bao", "bao", "steamed bun"],
    "bánh bèo": ["banh beo"],
    "bánh căn": ["banh can"],
    
    # Gỏi/Nộm variants
    "gỏi": ["goi", "nộm", "nom", "salad", "gỏi cuốn"],
    "nộm": ["nom", "gỏi"],
    "gỏi cuốn": ["goi cuon", "nem cuốn", "fresh rolls", "spring rolls"],
    
    # Nem/Chả variants
    "nem": ["nem rán", "chả giò", "fried spring rolls"],
    "chả giò": ["cha gio", "nem rán"],
    
    # Hải sản
    "hải sản": ["hai san", "seafood", "đồ biển", "hải sản tươi sống"],
    "seafood": ["hải sản", "hai san"],
    "tôm": ["tom", "shrimp", "tôm hùm", "tôm sú"],
    "cua": ["crab", "cua biển"],
    "mực": ["muc", "squid", "mực ống"],
    "ốc": ["oc", "snail", "ốc luộc"],
    
    # Thịt variants
    "thịt": ["thit", "meat", "heo", "bò", "gà"],
    "heo": ["lợn", "lon", "pork", "thịt heo"],
    "bò": ["bo", "beef", "thịt bò"],
    "gà": ["ga", "chicken", "thịt gà"],
    "vịt": ["vit", "duck", "thịt vịt"],
    "dê": ["de", "goat", "thịt dê"],
    
    # Món nướng
    "nướng": ["nuong", "grilled", "bbq", "nướng xiên", "nướng than", "nướng than hoa"],
    "bbq": ["nướng", "nuong", "barbecue"],
    "xiên nướng": ["xien nuong", "skewer", "꼬치"],
    
    # Chè/Tráng miệng
    "chè": ["che", "dessert", "tráng miệng", "chè bưởi", "chè đậu"],
    "kem": ["ice cream", "gelato", "kem tươi"],
    "sữa chua": ["sua chua", "yogurt", "yaourt"],
    
    # Cà phê
    "cà phê": ["ca phe", "coffee", "cafe", "cà  phê", "caphe", "cà phê sữa", "cà phê đen"],
    "ca phe": ["cà phê", "coffee", "cafe"],
    "coffee": ["cà phê", "ca phe", "cafe"],
    "cafe": ["cà phê", "ca phe", "coffee"],
    
    # Trà
    "trà": ["tra", "tea", "trà sữa", "trà đá", "trà chanh"],
    "tea": ["trà", "tra"],
    "trà sữa": ["tra sua", "milk tea", "bubble tea", "trà sữa trân châu"],
    
    # Nước ép/Sinh tố
    "sinh tố": ["sinh to", "smoothie", "nước ép"],
    "nước ép": ["nuoc ep", "juice", "sinh tố"],
    
    # Món Âu
    "steak": ["bít tết", "bit tet", "beefsteak"],
    "pasta": ["mì ý", "mi y", "spaghetti"],
    "pizza": ["bánh pizza", "bánh piza"],
    "burger": ["hamburger", "bánh mì kẹp"],
    "salad": ["sa lát", "rau trộn"],
    
    # Món Nhật
    "sushi": ["sushi nhật", "sushi cuộn"],
    "ramen": ["mì ramen", "ramen nhật"],
    "sashimi": ["sashimi nhật", "cá sống"],
    "tempura": ["tôm chiên xù"],
    "udon": ["mì udon"],
    
    # Món Hàn
    "kimchi": ["kim chi", "kim chi hàn quốc"],
    "bulgogi": ["thịt nướng hàn quốc"],
    "bibimbap": ["cơm trộn hàn quốc"],
    "tteokbokki": ["bánh gạo cay", "topokki"],
    "samgyeopsal": ["thịt ba chỉ nướng"],
    
    # Món Thái
    "tom yum": ["tôm yum", "lẩu thái"],
    "pad thai": ["mì xào thái"],
    "som tam": ["gỏi đu đủ"],
    
    # Món Trung
    "dimsum": ["dim sum", "điểm tâm", "há cảo"],
    "vịt quay": ["vit quay", "roasted duck"],
    "xá xíu": ["xa xiu", "char siu", "thịt xá xíu"],
    
    # EXPANDED SECTION: Vietnamese Slang & Colloquial Terms (700+ new terms)
    # Food Quality Descriptors
    "ngon": ["ngon", "delicious", "tasty", "đã", "tuyệt", "đỉnh", "chất", "đã quá", "ngon lành", "ngon tuyệt"],
    "chất lượng": ["chat luong", "quality", "đỉnh cao", "chất", "xịn", "xịn sò", "xịn xò", "xịn xó"],
    "tươi": ["tuoi", "fresh", "tươi rói", "tươi ngon", "tươi sống", "tươi mới"],
    "dở": ["dở", "bad", "tệ", "không ngon", "không ok", "không ổn"],
    
    # Price Slang (Vietnamese Teenagers)
    "rẻ": ["re", "cheap", "bình dân", "hạt dẻ", "bèo", "giá bèo", "vừa túi tiền", "hợp túi tiền", "không tốn kém", "tiết kiệm"],
    "đắt": ["dat", "expensive", "mắc", "mac", "chát", "giá cao", "xa xỉ", "đắt đỏ", "mắc mỏ", "chát quá"],
    "vừa túi tiền": ["vua tui tien", "affordable", "vừa phải", "phải chăng", "hợp lý", "ok wallet", "ổn túi"],
    "bao": ["bao nhiêu", "giá", "price", "how much", "cost", "chi phí", "tiền", "giá cả"],
    "miễn phí": ["mien phi", "free", "không mất tiền", "0 đồng", "không tốn", "free ship"],
    
    # Location Slang
    "gần": ["gan", "near", "nearby", "gần đây", "lân cận", "kế bên", "bên cạnh", "xung quanh", "around"],
    "xa": ["xa", "far", "xa quá", "xa xăm", "xa xôi", "đi lâu"],
    "thuận tiện": ["thuan tien", "convenient", "dễ tìm", "dễ đi", "easy to find"],
    "center": ["trung tâm", "trung tam", "center", "downtown", "giữa thành phố"],
    
    # Portion Size
    "no": ["no", "full", "đầy bụng", "no nê", "no căng", "no cứng", "배부른"],
    "nhiều": ["nhieu", "much", "many", "đầy", "full", "tràn", "hấp dẫn nhiều"],
    "ít": ["it", "little", "less", "thiếu", "ít ỏi"],
    "khổng lồ": ["khong lo", "huge", "to", "giant", "siêu to", "khủng"],
    "vừa đủ": ["vua du", "enough", "ok", "đủ ăn", "vừa phải"],
    
    # Service Quality
    "phục vụ": ["phuc vu", "service", "nhân viên", "staff", "bồi bàn"],
    "nhiệt tình": ["nhiet tinh", "enthusiastic", "chu đáo", "tốt", "friendly", "thân thiện"],
    "thái độ": ["thai do", "attitude", "manner", "cư xử"],
    "chậm": ["cham", "slow", "lâu", "delay", "chậm chạp", "lâu quá"],
    "nhanh": ["nhanh", "fast", "quick", "rapid", "mau", "tốc độ"],
    
    # Cooking Methods (Expanded)
    "xào": ["xao", "stir fry", "xào nấu", "rang"],
    "nấu": ["nau", "cook", "boil", "luộc", "hầm", "rim"],
    "hấp": ["hap", "steam", "steamed", "hấp dẫn"],
    "rim": ["rim", "simmer", "kho rim"],
    "quay": ["quay", "roast", "nướng vàng"],
    "áp chảo": ["ap chao", "pan-fry", "chiên áp chảo"],
    "rang": ["rang", "roast", "rang nấu", "rang giòn"],
    "om": ["om", "braise", "om nấu"],
    
    # Specific Vietnamese Dishes (Extended)
    "canh": ["canh", "soup", "súp", "soup light", "canh rau"],
    "cháo": ["chao", "porridge", "congee", "cháo dinh dưỡng"],
    "xôi": ["xoi", "sticky rice", "xôi xéo", "xôi gà"],
    "chả cá": ["cha ca", "grilled fish", "chả cá lã vọng"],
    "bún mắm": ["bun mam", "fermented fish noodle soup"],
    "cao lầu": ["cao lau", "cao lau hoi an"],
    "mì quảng": ["mi quang", "quang noodle"],
    "bánh canh": ["banh canh", "thick noodle soup", "bánh canh cua"],
    "bò kho": ["bo kho", "beef stew", "bò kho bánh mì"],
    "bò lúc lắc": ["bo luc lac", "shaking beef"],
    "cá kho tộ": ["ca kho to", "braised fish", "cá kho"],
    "thịt kho": ["thit kho", "braised pork", "thịt kho tàu", "thịt kho trứng"],
    "canh chua": ["canh chua", "sour soup", "canh chua cá"],
    "gà luộc": ["ga luoc", "boiled chicken"],
    "gà rán": ["ga ran", "fried chicken", "gà chiên"],
    "vịt nướng": ["vit nuong", "roasted duck"],
    "chân giò": ["chan gio", "pork knuckle", "chân giò hầm"],
    
    # Street Food (Ăn vặt)
    "bánh tráng": ["banh trang", "rice paper", "bánh đa", "bánh tráng trộn"],
    "chân gà": ["chan ga", "chicken feet", "chân gà sả ớt"],
    "nem chua": ["nem chua", "fermented pork roll", "nem chua rán"],
    "xíu mại": ["xiu mai", "meatball", "xíu mại trứng cút"],
    "bánh giò": ["banh gio", "rice cake wrap"],
    "bánh ướt": ["banh uot", "wet rice paper"],
    "bánh khọt": ["banh khot", "mini savory pancake"],
    "bánh flan": ["banh flan", "creme caramel", "flan"],
    "bánh đúc": ["banh duc", "plain flan cake"],
    "bánh bột lọc": ["banh bot loc", "tapioca dumpling"],
    "bánh ít": ["banh it", "small glutinous rice dumpling"],
    
    # Beverages (Expanded)
    "nước ngọt": ["nuoc ngot", "soft drink", "soda", "coca", "pepsi"],
    "nước suối": ["nuoc suoi", "water", "bottled water"],
    "bia": ["bia", "beer", "alcohol"],
    "rượu": ["ruou", "wine", "liquor", "alcohol"],
    "cocktail": ["cocktail", "mocktail", "mixed drink"],
    "sinh tố bơ": ["sinh to bo", "avocado smoothie"],
    "nước chanh": ["nuoc chanh", "lemon juice", "lemonade"],
    "trà chanh": ["tra chanh", "lemon tea"],
    "trá đá": ["tra da", "iced tea"],
    "cà phê đen": ["ca phe den", "black coffee"],
    "cà phê sữa": ["ca phe sua", "milk coffee"],
    "bạc xỉu": ["bac xiu", "white coffee"],
    
    # Atmosphere & Vibe Keywords
    "đẹp": ["dep", "beautiful", "nice", "pretty", "xinh", "lung linh"],
    "view": ["view", "cảnh", "canh", "view đẹp", "scenic view", "tầng cao"],
    "sân vườn": ["san vuon", "garden", "outdoor", "ngoài trời"],
    "âm nhạc": ["am nhac", "music", "nhạc sống", "live music"],
    "rộng rãi": ["rong rai", "spacious", "thoáng", "wide"],
    "hẹp": ["hep", "narrow", "chật", "small"],
    "mát mẻ": ["mat me", "cool", "air conditioned", "có máy lạnh"],
    "nóng": ["nong", "hot", "nóng nực", "stuffy"],
    "sạch sẽ": ["sach se", "clean", "tidy", "ngăn nắp"],
    "bẩn": ["ban", "dirty", "messy", "không sạch"],
    "sang chảnh": ["sang chanh", "fancy", "luxurious", "high class", "đẳng cấp"],
    
    # Time-related
    "sáng": ["sang", "morning", "breakfast", "ăn sáng"],
    "trưa": ["trua", "noon", "lunch", "ăn trưa"],
    "chiều": ["chieu", "afternoon", "tea time", "ăn chiều"],
    "tối": ["toi", "evening", "night", "dinner", "ăn tối"],
    "khuya": ["khuya", "late night", "midnight", "đêm"],
    "mở cửa": ["mo cua", "open", "opening hours", "giờ mở cửa"],
    "đóng cửa": ["dong cua", "closed", "closing time"],
    "24/7": ["24/7", "24h", "suốt ngày đêm", "mở cả ngày"],
    
    # Occasion Keywords
    "sinh nhật": ["sinh nhat", "birthday", "party", "tiệc"],
    "hẹn hò": ["hen ho", "date", "dating", "người yêu", "couple"],
    "gia đình": ["gia dinh", "family", "bạn bè", "friends", "tụ tập"],
    "công ty": ["cong ty", "company", "team", "đồng nghiệp"],
    "họp mặt": ["hop mat", "gathering", "meeting", "reunion"],
    "tiệc": ["tiec", "party", "buffet", "event", "tiệc buffet"],
    
    # Dietary Preferences
    "chay": ["chay", "vegetarian", "vegan", "không thịt", "an chay"],
    "halal": ["halal", "muslim", "islam", "halal food"],
    "không cay": ["khong cay", "not spicy", "mild", "nhẹ", "không매운"],
    "cay": ["cay", "spicy", "hot", "cay nồng", "매운"],
    "ngọt": ["ngot", "sweet", "sweetened"],
    "mặn": ["man", "salty", "savory"],
    "chua": ["chua", "sour", "acidic"],
    "béo": ["beo", "fatty", "oily", "nhiều dầu"],
    "thanh đạm": ["thanh dam", "light", "plain", "simple"],
    
    # Special Features
    "wifi": ["wifi", "wi-fi", "internet", "mạng"],
    "điều hòa": ["dieu hoa", "air conditioner", "ac", "máy lạnh"],
    "chỗ đậu xe": ["cho dau xe", "parking", "đỗ xe", "bãi đỗ"],
    "ship": ["ship", "delivery", "giao hàng", "đặt ship", "order"],
    "đặt trước": ["dat truoc", "reservation", "book", "booking"],
    "không gian riêng": ["khong gian rieng", "private room", "phòng riêng"],
    "kids friendly": ["kids friendly", "trẻ em", "khu vui chơi", "children area"],
    "pet friendly": ["pet friendly", "thú cưng", "pets allowed"],
    
    # Popular Chains & International Foods
    "kfc": ["kfc", "kentucky", "gà rán kfc"],
    "lotteria": ["lotteria", "burger lotteria"],
    "pizza hut": ["pizza hut", "pizza"],
    "domino": ["domino", "domino's pizza"],
    "highland": ["highlands", "highlands coffee", "highland coffee"],
    "starbucks": ["starbucks", "starbuck", "cà phê starbucks"],
    "jollibee": ["jollibee", "gà jollibee"],
    "texas chicken": ["texas chicken", "texas"],
    
    # Cuisine-specific Ingredients
    "phô mai": ["pho mai", "cheese", "fromage"],
    "bơ": ["bo", "butter", "avocado", "bơ tươi"],
    "sữa": ["sua", "milk", "dairy"],
    "trứng": ["trung", "egg", "eggs"],
    "rau": ["rau", "vegetable", "veggies", "greens"],
    "nấm": ["nam", "mushroom", "fungus"],
    "đậu": ["dau", "beans", "tofu", "đậu hủ"],
    "măng": ["mang", "bamboo shoot"],
    "khoai": ["khoai", "potato", "sweet potato", "khoai tây"],
    
    # Modern Food Trends
    "organic": ["organic", "hữu cơ", "sạch", "clean eating"],
    "healthy": ["healthy", "lành mạnh", "ăn khỏe", "dinh dưỡng"],
    "low carb": ["low carb", "ít tinh bột", "keto"],
    "protein": ["protein", "đạm", "high protein"],
    "detox": ["detox", "thanh lọc", "giải độc"],
    "smoothie bowl": ["smoothie bowl", "bowl ngon"],
    "poke bowl": ["poke bowl", "cơm hawaii"],
    "acai bowl": ["acai bowl", "bowl siêu thực phẩm"],
}

CUISINE_TYPES = {
    # Country-based cuisines
    "vietnamese": ["việt nam", "viet nam", "vietnamese", "vn", "việt"],
    "japanese": ["nhật", "nhật bản", "japan", "japanese", "sushi", "sashimi", "ramen"],
    "korean": ["hàn", "hàn quốc", "korea", "korean", "kimchi", "bulgogi"],
    "thai": ["thái", "thái lan", "thailand", "thai", "tom yum"],
    "chinese": ["trung", "trung quốc", "china", "chinese", "dimsum", "dim sum"],
    "western": ["âu", "tây", "western", "europe", "european"],
    "italian": ["ý", "italy", "italian", "pizza", "pasta", "spaghetti"],
    "french": ["pháp", "france", "french"],
    
    # Dish-based cuisines (Vietnamese dishes)
    "phở": ["phở", "pho"],
    "bún": ["bún", "bun"],
    "cơm": ["cơm", "com", "rice"],
    "bánh mì": ["bánh mì", "banh mi"],
    "mì": ["mì", "mi", "noodle"],
    "lẩu": ["lẩu", "lau", "hotpot", "hot pot"],
    "nướng": ["nướng", "nuong", "grill", "bbq", "barbe", "nướng"],
    "hải sản": ["hải sản", "hai san", "seafood", "ốc", "tôm", "cua", "cá"],
    "buffet": ["buffet", "buffet"],
    "cafe": ["cafe", "cà phê", "coffee", "ca phe"],
    "trà": ["trà", "tra", "tea", "trà sữa", "tra sua"],
    "chay": ["chay", "vegetarian", "vegan", "đồ chay"],
    "nem": ["nem", "spring roll", "chả giò", "cha gio"],
    "hủ tiếu": ["hủ tiếu", "hu tieu"],
    "bánh xèo": ["bánh xèo", "banh xeo"],
    "bún chả": ["bún chả", "bun cha"],
    "cơm tấm": ["cơm tấm", "com tam"],
    
    # Cooking methods & food types (CRITICAL - these were missing!)
    "món chiên": ["món chiên", "mon chien", "chiên", "chien", "fried", "rán", "ran"],
    "món xào": ["món xào", "mon xao", "xào", "xao", "stir fry", "stir-fry"],
    "món kho": ["món kho", "mon kho", "kho", "braised", "stew"],
    "món nước": ["món nước", "mon nuoc", "nước", "nuoc", "soup", "canh"],
    "món gỏi": ["món gỏi", "mon goi", "gỏi", "goi", "salad"],
    "ăn vặt": ["ăn vặt", "an vat", "snack", "tráng miệng", "trang mieng", "dessert"],
    
    # Meat types
    "gà": ["gà", "ga", "chicken"],
    "bò": ["bò", "bo", "beef"],
    "heo": ["heo", "pork", "lợn", "lon"],
    "vịt": ["vịt", "vit", "duck"],
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
