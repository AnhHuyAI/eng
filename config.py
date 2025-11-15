# config.py - Root level configuration

import os
from datetime import timedelta
from app.config import Config as AppConfig, DevelopmentConfig as AppDevelopmentConfig, ProductionConfig as AppProductionConfig

# Re-export app config classes
Config = AppConfig
DevelopmentConfig = AppDevelopmentConfig
ProductionConfig = AppProductionConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
