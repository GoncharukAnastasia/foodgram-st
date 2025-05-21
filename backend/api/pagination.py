from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Кастомный пагинатор."""
    page_size = 6
    page_size_query_param = 'limit'
