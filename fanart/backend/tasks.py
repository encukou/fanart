import json

from fanart.tasks import task_functions
from fanart.models import tables

def schedule_task(backend, name, params, priority=None):
    if priority is None:
        priority, func = task_functions[name]
    task = tables.Task(
        name=name,
        params=json.dumps(params),
        priority=priority)
    backend._db.add(task)
    backend._db.flush()
    return task.id

def run_task(backend, n=1):
    return_values = []
    for i, task in enumerate(get_tasks(backend), start=1):
        priority, func = task_functions[task.name]
        print()
        print('Running task {} with {}'.format(task.name, task.params))
        params = json.loads(task.params)
        return_value = func(backend, **params)
        return_values.append((task.name, params, return_value))
        print('Done task {} with {}'.format(task.name, task.params))
        print()
        backend._db.delete(task)
        backend._db.commit()
        if n and i >= n:
            break
    return return_values

def get_tasks(backend):
    while True:
        query = backend._db.query(tables.Task)
        query = query.order_by(tables.Task.priority.desc())
        tasks = query[:10]
        if tasks:
            for task in tasks:
                yield task
        else:
            return
