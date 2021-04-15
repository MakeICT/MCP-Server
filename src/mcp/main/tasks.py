import sys

from rq import get_current_job
from mcp import create_app, db
from mcp.main.models import Task


def set_task_progress(progress, status=None):
    print(f"set task progress: {progress}")
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress,
                                                     'status': status})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def run_as_task(func, *args, **kwargs):
    app = create_app()
    app.app_context().push()

    # print("ARGS:", args)

    try:
        func(*args, **kwargs)
        set_task_progress(100)
    except:
        set_task_progress(100, 'failed')
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
