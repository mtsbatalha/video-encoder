# Avoid circular imports - use explicit imports where needed
# from .profile_manager import ProfileManager
# from .job_manager import JobManager
# from .queue_manager import QueueManager
# from .stats_manager import StatsManager
# from .config_manager import ConfigManager
# from .recurrent_folder_manager import RecurrentFolderManager
# from .recurrent_history_manager import RecurrentHistoryManager
# from .multi_profile_conversion_manager import MultiProfileConversionManager, ConversionPlan, PlannedJob, NamingConvention

__all__ = [
    'ProfileManager',
    'JobManager',
    'QueueManager',
    'StatsManager',
    'ConfigManager',
    'RecurrentFolderManager',
    'RecurrentHistoryManager',
    'MultiProfileConversionManager',
    'ConversionPlan',
    'PlannedJob',
    'NamingConvention'
]
