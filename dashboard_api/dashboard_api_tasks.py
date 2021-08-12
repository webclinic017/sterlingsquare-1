from celery.decorators import task
from .views import DailyUpdatePortfolioPerformanceData

@task
def get_dashboard_app_api_task():
    print("---Dashboard_Api_App task started---")
    DailyUpdatePortfolioPerformanceData()
    print("---Dashboard_Api_App task ended---")

