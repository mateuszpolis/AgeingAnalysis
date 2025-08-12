import datetime

from ageing_analysis.services.cfd_rate_integration_service import (
    CFDRateIntegrationService,
)

cfd_rate_integration_service = CFDRateIntegrationService()

result = cfd_rate_integration_service.get_integrated_cfd_rate(
    datetime.datetime(2023, 6, 21),
    datetime.datetime(2023, 7, 27),
    multiply_by_mu=True,
    use_latest_available_configuration=True,
)
