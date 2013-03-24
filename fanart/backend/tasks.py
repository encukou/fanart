import json

from fanart.models import tables
from fanart.tasks import image
from fanart import AVATAR_SIZE

def schedule_task(backend, name, params, priority=None):
    if priority is None:
        priority, func = tasks_functions[name]
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
        priority, func = tasks_functions[task.name]
        print('Running task {} with {}'.format(task.name, task.params))
        return_values.append(func(backend, **json.loads(task.params)))
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

tasks_functions = {}

def register(name_or_func=None, priority=0):
    if callable(name_or_func):
        tasks_functions[name_or_func.__name__] = priority, name_or_func
    else:
        def register(func):
            tasks_functions[name_or_func or func.__name__] = priority, func
        return register

@register
def apply_avatar(backend, user_id):
    user = backend.users[user_id]._obj
    if user.avatar_request:
        print('Identifying artifact {}'.format(user.avatar_request.id))
        if not image.identify_artifact(backend, user.avatar_request):
            print('Identification failed!')
        if user.gender == 'female':
            w = 'uživatelky'
        else:
            w = 'uživatele'
        comment = 'Avatar {} {} na poke.fanart.cz'.format(w, user.name)
        print('Resizing avatar for user {}'.format(user.id))
        new_avatar = image.resize_image(
            backend, user.avatar_request, 'png', AVATAR_SIZE, AVATAR_SIZE,
            comment=comment)
        if new_avatar:
            user.avatar = new_avatar
            backend.schedule_task(
                'remove_artifact', {'artifact_id': user.avatar_request.id})
            user.avatar_request = None

@register(priority=-100)
def remove_artifact(backend, artifact_id):
    raise NotImplementedError()
