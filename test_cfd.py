import datetime

from ageing_analysis.services.cfd_rate_integration_service import (
    CFDRateIntegrationService,
)

cfd_rate_integration_service = CFDRateIntegrationService()

result = cfd_rate_integration_service.get_integrated_cfd_rate(
    datetime.datetime(2022, 6, 1),
    datetime.datetime(2024, 5, 31),
    multiply_by_mu=True,
)
