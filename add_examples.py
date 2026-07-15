import os

dash_dto_path = 'backend/domains/investments/dashboard_dto.py'

with open(dash_dto_path, 'r', encoding='utf-8') as f:
    dash_dto_content = f.read()

# Add to dashboard_dto.py
if 'model_config' not in dash_dto_content:
    dash_dto_content = dash_dto_content.replace('class PortfolioDashboardDTO(BaseModel):', '''class PortfolioDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_wealth": 22930.00,
                "unrealized_gain": 2930.00,
                "unrealized_gain_percent": 14.65,
                "twr": 12.5,
                "mwr": 13.82,
                "sharpe": 1.2,
                "max_drawdown": -5.4
            }
        }
    }''')
    dash_dto_content = dash_dto_content.replace('class AllocationDashboardDTO(BaseModel):', '''class AllocationDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "by_asset": [{"ticker": "PETR4", "percentage": 25.0}],
                "by_class": [{"asset_class": "STOCK", "percentage": 60.0}],
                "by_institution": [{"institution": "XP", "percentage": 100.0}]
            }
        }
    }''')
    dash_dto_content = dash_dto_content.replace('class PerformanceDashboardDTO(BaseModel):', '''class PerformanceDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "monthly_return": 1.2,
                "annual_return": 14.5,
                "benchmark_comparison": {"ibov": 0.8},
                "rolling_returns": {"12m": 12.0}
            }
        }
    }''')
    dash_dto_content = dash_dto_content.replace('class RiskDashboardDTO(BaseModel):', '''class RiskDashboardDTO(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "volatility": 15.2,
                "current_drawdown": -2.1,
                "sharpe": 1.2,
                "sortino": 1.5,
                "beta": 0.9
            }
        }
    }''')
    
    with open(dash_dto_path, 'w', encoding='utf-8') as f:
        f.write(dash_dto_content)

print('Added examples to dashboard_dto.py')
