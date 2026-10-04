"""
Personal Shopping Agent - Main Flask Application Entry Point.
AI-Powered Product Price Comparison, Review Analysis, and Smart Recommendation System.
"""

import os
import logging
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
import sys
from pathlib import Path

# Add project root to sys.path so both direct execution and package execution succeed
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from .config import config_by_name, Config
    from .database.db import db
    from .database.init_db import init_database
    from .database.models import SearchHistory, Product
    from .services.search_service import SearchService
    from .services.comparison_service import ComparisonService
    from .services.product_service import ProductService
    from .services.review_service import ReviewService
    from .services.recommendation_service import RecommendationService
    from .utils.validators import validate_search_filters
    from .utils.price_utils import format_inr
    from .utils.helpers import (
        format_datetime,
        truncate_text,
        get_sentiment_color,
        get_star_rating_breakdown,
    )
except (ImportError, ValueError):
    from config import config_by_name, Config
    from database.db import db
    from database.init_db import init_database
    from database.models import SearchHistory, Product
    from services.search_service import SearchService
    from services.comparison_service import ComparisonService
    from services.product_service import ProductService
    from services.review_service import ReviewService
    from services.recommendation_service import RecommendationService
    from utils.validators import validate_search_filters
    from utils.price_utils import format_inr
    from utils.helpers import (
        format_datetime,
        truncate_text,
        get_sentiment_color,
        get_star_rating_breakdown,
    )


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("personal_shopping_agent")


def create_app(config_name: str = "default") -> Flask:
    """Application factory for Personal Shopping Agent."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    # Load configuration
    cfg = config_by_name.get(config_name, Config)
    app.config.from_object(cfg)

    # Ensure instance directory exists for SQLite database
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize SQLAlchemy database
    db.init_app(app)

    # Initialize tables and seed records
    init_database(app)

    # Register Jinja2 template filters
    @app.template_filter("inr")
    def inr_filter(value):
        return format_inr(value)

    @app.template_filter("datetime_fmt")
    def datetime_filter(value):
        return format_datetime(value)

    @app.template_filter("truncate_chars")
    def truncate_filter(value, length=100):
        return truncate_text(value, length)

    @app.template_filter("sentiment_badge")
    def sentiment_badge_filter(value):
        return get_sentiment_color(value)

    @app.template_filter("stars")
    def stars_filter(value):
        return get_star_rating_breakdown(value)

    # Context processors for global template variables
    @app.context_processor
    def inject_global_data():
        return {
            "app_name": "Personal Shopping Agent",
            "categories": Config.CATEGORIES,
            "supported_websites": Config.SUPPORTED_WEBSITES,
            "sort_options": Config.SORT_OPTIONS,
            "use_sample_data": app.config.get("USE_SAMPLE_DATA", True),
        }

    # Initialize services
    search_service = SearchService()
    comparison_service = ComparisonService()
    product_service = ProductService()
    review_service = ReviewService()
    recommendation_service = RecommendationService()

    # -------------------------------------------------------------
    # ROUTES
    # -------------------------------------------------------------

    @app.route("/")
    def index():
        """Homepage with featured search form and quick categories."""
        # Retrieve recent searches for quick repeat
        recent_searches = (
            SearchHistory.query.order_by(SearchHistory.search_timestamp.desc())
            .limit(5)
            .all()
        )
        return render_template("index.html", recent_searches=[s.to_dict() for s in recent_searches])


    @app.route("/search", methods=["GET", "POST"])
    def search():
        """Handles search submissions from both GET and POST requests."""
        params = request.form.to_dict() if request.method == "POST" else request.args.to_dict()

        is_valid, cleaned, errors = validate_search_filters(params)
        if not is_valid:
            for err in errors:
                flash(err, "warning")
            return redirect(url_for("index"))

        # Redirect to GET /products with clean query parameters
        query_args = {"q": cleaned["query"]}
        if cleaned.get("category"):
            query_args["category"] = cleaned["category"]
        if cleaned.get("min_price") is not None:
            query_args["min_price"] = cleaned["min_price"]
        if cleaned.get("max_price") is not None:
            query_args["max_price"] = cleaned["max_price"]
        if cleaned.get("website"):
            query_args["website"] = cleaned["website"]
        if cleaned.get("min_rating") is not None:
            query_args["min_rating"] = cleaned["min_rating"]
        if cleaned.get("brand"):
            query_args["brand"] = cleaned["brand"]
        if cleaned.get("sort_by"):
            query_args["sort_by"] = cleaned["sort_by"]

        return redirect(url_for("products", **query_args))

    @app.route("/products")
    def products():
        """Displays filtered product search results in responsive cards."""
        params = request.args.to_dict()
        is_valid, cleaned, errors = validate_search_filters(params)

        if not is_valid and not params.get("q"):
            flash("Please enter a product name to search.", "info")
            return redirect(url_for("index"))

        search_result = search_service.search_products(cleaned)

        return render_template(
            "products.html",
            query=cleaned.get("query", ""),
            products=search_result["products"],
            total_count=search_result["total_count"],
            lowest_product=search_result["lowest_product"],
            filters=cleaned,
        )

    @app.route("/compare", methods=["GET", "POST"])
    def compare():
        """Compares selected products side-by-side with lowest-price highlighting."""
        product_ids = []
        if request.method == "POST":
            # Handles list of checkboxes from comparison form
            product_ids = request.form.getlist("product_ids")
        else:
            ids_param = request.args.get("ids", "")
            if ids_param:
                product_ids = [pid.strip() for pid in ids_param.split(",") if pid.strip()]

        if not product_ids:
            flash("Please select at least 2 products to compare prices.", "info")
            return redirect(url_for("index"))

        comparison_data = comparison_service.compare_products_by_ids(product_ids)
        return render_template("compare.html", **comparison_data)

    @app.route("/details/<product_id>")
    def details(product_id: str):
        """Displays detailed specifications, price history chart, and reviews."""
        product = product_service.get_product_by_id(product_id)
        if not product:
            abort(404, description=f"Product with ID '{product_id}' was not found.")

        # Find price history for Chart.js
        price_history = product_service.get_price_history(product_id)

        # Find equivalent store offers for quick comparison
        equivalent_offers = comparison_service.find_equivalent_store_offers(product_id)

        # Get or generate review sentiment analysis
        review_analysis = review_service.get_or_analyze_reviews(product_id)

        return render_template(
            "details.html",
            product=product.to_dict(),
            price_history=price_history,
            equivalent_offers=equivalent_offers,
            review_analysis=review_analysis,
        )

    @app.route("/recommendations", methods=["GET", "POST"])
    def recommendations():
        """Generates AI-powered product recommendations for a query or category."""
        query = request.args.get("q") or request.form.get("query") or ""
        recs = recommendation_service.get_recommendations_for_query(query)

        return render_template(
            "recommendations.html",
            query=query,
            lowest_pick=recs.get("lowest_price_pick"),
            best_rated_pick=recs.get("best_rated_pick"),
            best_overall_pick=recs.get("best_overall_pick"),
            ranked_products=recs.get("ranked_products", []),
        )

    @app.route("/reviews/<product_id>")
    def reviews(product_id: str):
        """Dedicated customer review analysis view."""
        product = product_service.get_product_by_id(product_id)
        if not product:
            abort(404, description="Product not found.")

        analysis = review_service.get_or_analyze_reviews(product_id)
        return render_template(
            "details.html",
            product=product.to_dict(),
            price_history=product_service.get_price_history(product_id),
            equivalent_offers=comparison_service.find_equivalent_store_offers(product_id),
            review_analysis=analysis,
            active_tab="reviews",
        )

    @app.route("/history")
    def history():
        """Shows user search history with timestamp and repeat search links."""
        searches = (
            SearchHistory.query.order_by(SearchHistory.search_timestamp.desc())
            .limit(50)
            .all()
        )
        return render_template("history.html", searches=[s.to_dict() for s in searches])

    @app.route("/history/clear", methods=["POST"])
    def clear_history():
        """Clears local search history."""
        try:
            SearchHistory.query.delete()
            db.session.commit()
            flash("Search history cleared successfully.", "success")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error clearing search history: {e}")
            flash("An error occurred while clearing search history.", "danger")

        return redirect(url_for("history"))

    @app.route("/api/search", methods=["POST"])
    def api_search():
        """JSON search endpoint for API consumers."""
        data = request.get_json(silent=True) or request.form.to_dict()
        is_valid, cleaned, errors = validate_search_filters(data)
        if not is_valid:
            return jsonify({"status": "error", "errors": errors}), 400

        result = search_service.search_products(cleaned)
        return jsonify({
            "status": "success",
            "query": result["query"],
            "total_count": result["total_count"],
            "lowest_product": result["lowest_product"],
            "products": result["products"],
        })

    @app.route("/health")
    def health():
        """Application health check endpoint."""
        total_products = Product.query.count()
        return jsonify({
            "status": "healthy",
            "application": "Personal Shopping Agent",
            "database_connected": True,
            "catalog_count": total_products,
        })

    @app.route("/about")
    def about():
        """About page explaining architecture, ethical scraping, and scoring."""
        return render_template("about.html")

    # -------------------------------------------------------------
    # ERROR HANDLERS
    # -------------------------------------------------------------

    @app.errorhandler(404)
    def page_not_found(e):
        return (
            render_template(
                "error.html",
                error_code=404,
                title="Page Not Found",
                message=getattr(e, "description", "The requested page or product could not be found."),
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return (
            render_template(
                "error.html",
                error_code=500,
                title="Internal Server Error",
                message="An unexpected system error occurred. Our engineers have been alerted.",
            ),
            500,
        )

    return app


# Create default app instance for wsgi / direct execution
app = create_app(os.getenv("FLASK_ENV", "default"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("DEBUG", "True").lower() in ("true", "1")
    print(f"\n=================================================================")
    print(f"  Personal Shopping Agent - AI Smart Shopping & Price Comparison")
    print(f"  Server starting at: http://127.0.0.1:{port}")
    print(f"=================================================================\n")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
