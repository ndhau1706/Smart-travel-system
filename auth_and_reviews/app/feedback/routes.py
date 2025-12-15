from flask import Blueprint, request, jsonify
from sqlalchemy import desc, asc
from ..extensions import db
from .models import Review
from .utils import token_required, calculate_hybrid_score
from datetime import datetime, timezone 
# Khởi tạo Blueprint
feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/add', methods=['POST'])
@token_required
def add_review(current_user):
    data = request.get_json()
    
    # 1. Lấy dữ liệu từ Frontend gửi lên
    place_id = data.get('place_id')
    rating = data.get('rating') # Bắt buộc phải là số (1-5)
    raw_content = data.get('content')
    content = str(raw_content) if raw_content is not None else ""
    
    # 2. Kiểm tra dữ liệu đầu vào (Validation)
    if not place_id or rating is None:
        return jsonify({"message": "Thiếu thông tin place_id hoặc rating"}), 400

    try:
        # 3. Duplicate Check (Chống Spam)
        # Kiểm tra xem user này đã review quán này chưa
        existing_review = Review.query.filter_by(
            user_id=current_user.id, 
            place_id=place_id
        ).first()

        if existing_review:
            # Nếu có rồi -> Báo lỗi 409 Conflict (Trùng lặp)
            return jsonify({
                "message": "Bạn đã đánh giá địa điểm này rồi. Vui lòng sửa đánh giá cũ."
            }), 409 

        # 4. Hybrid Sentiment Calculation (Tính điểm lai)
        # Gọi hàm từ utils.py để tính toán
        # Hàm này trả về 2 giá trị: Điểm thang 10 (float) và Nhãn (string)
        final_score, sentiment_label = calculate_hybrid_score(int(rating), content)

        # 5. Tạo Object Review để lưu
        new_review = Review(
            user_id=current_user.id,
            place_id=place_id,
            rating=rating,
            content=content,
            sentiment=sentiment_label, # Ví dụ: 'Positive'
            final_score=final_score    # Ví dụ: 8.5
        )

        # 6. Lưu vào Database
        db.session.add(new_review)
        db.session.commit()

        return jsonify({
            "message": "Review created successfully",
            "data": new_review.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback() # Hoàn tác nếu lỗi
        return jsonify({"message": "Lỗi Server", "error": str(e)}), 500


@feedback_bp.route('/public/<place_id>', methods=['GET'])
def get_public_reviews(place_id):
    # 1. Lấy tham số từ URL (Query Params)
    # Ví dụ: /public/123?sort_by=highest&page=2
    sort_by = request.args.get('sort_by', 'newest') # Mặc định là 'newest'
    page = request.args.get('page', 1, type=int)    # Mặc định là trang 1
    per_page = 5 # Giới hạn 5 item/trang theo tài liệu

    # 2. Tạo Query cơ bản: Lấy review của quán này
    query = Review.query.filter_by(place_id=place_id)

    # 3. Xử lý Logic Sắp xếp (Sorting Strategy)
    if sort_by == 'highest':
        # Ưu tiên bài có Final Score cao nhất (User khen + AI tích cực)
        query = query.order_by(desc(Review.final_score))
    elif sort_by == 'lowest':
        # Đẩy bài có Final Score thấp nhất lên đầu (Cảnh báo rủi ro)
        query = query.order_by(asc(Review.final_score))
    else: 
        # 'newest' - Mặc định: Mới nhất lên đầu
        query = query.order_by(desc(Review.created_at))

    # 4. Phân trang (Pagination)
    # error_out=False: Nếu xin trang 100 mà ko có thì trả về list rỗng chứ ko báo lỗi 404
    paginated_reviews = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 5. Chuyển đổi dữ liệu sang JSON
    results = [r.to_dict() for r in paginated_reviews.items]

    return jsonify({
        "place_id": place_id,
        "total_reviews": paginated_reviews.total, # Tổng số review
        "total_pages": paginated_reviews.pages,   # Tổng số trang
        "current_page": page,
        "data": results
    }), 200

@feedback_bp.route('/me', methods=['GET'])
@token_required
def get_my_reviews(current_user):
    # 1. Lấy tham số place_id từ URL (nếu có)
    # Ví dụ: /me?place_id=quan-ngon-123
    place_id = request.args.get('place_id')

    # 2. Query cơ bản: Lấy tất cả review của user này
    query = Review.query.filter_by(user_id=current_user.id)

    # 3. [QUY TRÌNH 4.4] Optional Filter by Restaurant
    # Nếu có place_id -> Lọc thêm theo quán để user quản lý review tại quán đó
    if place_id:
        query = query.filter_by(place_id=place_id)
    
    # 4. Sắp xếp & Trả về
    results = query.order_by(desc(Review.created_at)).all()
    
    return jsonify([r.to_dict() for r in results]), 200

@feedback_bp.route('/delete/<review_id>', methods=['DELETE'])
@token_required
def delete_review(current_user, review_id):
    try:
        # [QUY TRÌNH 4.3] Resource Lookup
        # Tìm review trong DB theo ID
        review = Review.query.get(review_id)

        # Nếu không tìm thấy
        if not review:
            return jsonify({"message": "Review not found"}), 404

        # [QUY TRÌNH 4.3] Identity Resolution (Owner Check)
        # So sánh: ID người tạo review (trong DB) vs ID người đang request (Token)
        # Chuyển về string để so sánh cho chắc ăn vì UUID object đôi khi khó so sánh trực tiếp
        if str(review.user_id) != str(current_user.id):
            return jsonify({
                "message": "Access Denied. Bạn không có quyền xóa bài viết của người khác."
            }), 403 # Forbidden

        # [QUY TRÌNH 4.3] Hard Delete (Xóa vĩnh viễn)
        db.session.delete(review)
        db.session.commit()

        return jsonify({"message": "Deleted Permanently"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Lỗi Server", "error": str(e)}), 500
    
@feedback_bp.route('/update/<review_id>', methods=['PUT']) 
@token_required
def update_review(current_user, review_id):
    try:
        data = request.get_json()
        
        # 1. Tìm Review
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"message": "Review not found"}), 404

        # 2. Check quyền sở hữu (Owner Check)
        if str(review.user_id) != str(current_user.id):
            return jsonify({
                "message": "Access Denied. Bạn không có quyền sửa bài viết này."
            }), 403

        # 3. Cập nhật dữ liệu & Đánh dấu thay đổi
        has_changed = False
        
        # --- Update Rating ---
        if 'rating' in data:
            new_rating = int(data['rating'])
            if not (1 <= new_rating <= 5):
                 return jsonify({"message": "Rating phải từ 1 đến 5"}), 400
            
            if new_rating != review.rating:
                review.rating = new_rating
                has_changed = True

        # --- Update Content ---
        if 'content' in data:
            new_content = data['content']
            if new_content != review.content:
                review.content = new_content
                has_changed = True

        # 4. TÍNH TOÁN LẠI (Nếu có thay đổi)
        if has_changed:
            # Tái sử dụng hàm calculate_hybrid_score từ utils.py
            # Hàm này tự động: Dịch -> Phân tích Sentiment -> Tính toán lại điểm -> Trả về tuple
            new_score, new_sentiment = calculate_hybrid_score(review.rating, review.content)
            
            # Cập nhật kết quả mới vào model
            review.final_score = new_score
            review.sentiment = new_sentiment
            
            # Cập nhật thời gian sửa đổi (UTC)
            review.updated_at = datetime.now(timezone.utc)
            db.session.commit()

            return jsonify({
                "message": "Cập nhật thành công",
                "review": review.to_dict()
            }), 200
        
        else:
            return jsonify({"message": "Không có thay đổi nào được thực hiện"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Update Review: {str(e)}")
        return jsonify({"message": "Lỗi Server", "error": str(e)}), 500