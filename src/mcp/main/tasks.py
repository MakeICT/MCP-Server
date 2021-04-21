import sys

from rq import get_current_job
from mcp import create_app, db
from mcp.main.models import Task


def set_task_progress(progress, status=None, details=None):
    print(f"set task progress: {progress}")
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress,
                                                     'status': status,
                                                     'details': details})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def run_as_task(func, *args, **kwargs):
    app = create_app()
    app.app_context().push()

    # print("ARGS:", args)
    app.logger.info(f'Adding task {func.__name__} to RQ')
    try:
        func(*args, **kwargs)
        set_task_progress(100)
        app.logger.info(f'Task {func.__name__} completed successfully')
    except Exception as e:
        db.session.rollback()
        m = getattr(e, 'message', repr(e)).encode().decode('unicode_escape')
        set_task_progress(100, 'failed', m)
        app.logger.error(f'{func.__name__} failed due to unhandled exception', exc_info=sys.exc_info())
