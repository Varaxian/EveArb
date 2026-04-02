Version: v2.06 patch hotfix

Replace:
- apps/api/app/services/scheduler_service.py

Delete:
- none

Commit message:
v2.06 hotfix - fix scheduler settings_service import

Cause:
- scheduler_service still imported get_tracked_regions after settings_service
  was renamed to use platform/user-specific helpers.
- Railway crash: ImportError for get_tracked_regions. fileciteturn6file0
