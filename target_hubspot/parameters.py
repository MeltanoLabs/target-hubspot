"""
TUNING PARAMETERS
Keeping any tuning parameters centrally located here for convenience
"""

HUBSPOT_TIME_BETWEEN_RETRIES = 15
HUBSPOT_TIMEOUT_MINUTES = 5

MELTANO_MAX_BATCH_SIZE = 100 # HubSpot is conflicting and their docs say they support anywhere from 100 to 1000 max in batch endpoints; we go with the lower end to be safe