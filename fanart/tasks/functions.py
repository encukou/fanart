import os

from sqlalchemy.orm import joinedload_all

from fanart.models import tables
from fanart.tasks import image
from fanart import AVATAR_SIZE, THUMB_SIZE, VIEW_SIZE

task_functions = {}

def register(name_or_func=None, priority=0):
    if callable(name_or_func):
        task_functions[name_or_func.__name__] = priority, name_or_func
    else:
        def register(func):
            task_functions[name_or_func or func.__name__] = priority, func
        return register

@register
def apply_avatar(backend, user_id):
    user = backend._db.query(tables.User).get(user_id)
    if user.avatar_request:
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

@register
def process_art(backend, version_id):
    db = backend._db
    query = db.query(tables.ArtworkVersion)
    query = query.filter(tables.ArtworkVersion.id == version_id)
    query = query.options(joinedload_all('artwork_artifacts', 'artifact'))
    artwork_version = query.one()
    scratch_artifact = artwork_version.artifacts.get('scratch')
    if not scratch_artifact:
        return
    thumb = artwork_version.artifacts.get('thumb')
    view = artwork_version.artifacts.get('view')
    full = artwork_version.artifacts.get('full')
    if not thumb:
        image.process_image(backend, artwork_version, scratch_artifact,
                            THUMB_SIZE, 'thumb')
    elif not view:
        image.process_image(backend, artwork_version, scratch_artifact,
                            VIEW_SIZE, 'view', base=(thumb, THUMB_SIZE))
    elif not full:
        image.process_image(backend, artwork_version, scratch_artifact,
                            None, 'full', base=(view, VIEW_SIZE),
                            keep_animations=True)
        artwork_version.artwork.complete = True
        db.delete(artwork_version.artwork_artifacts['scratch'])
        backend.schedule_task('remove_artifact',
                              {'artifact_id': scratch_artifact.id})
        backend.schedule_task('try_publish_art',
                              {'artwork_id': artwork_version.artwork_id})
        return
    backend.schedule_task('process_art', {'version_id': version_id})


@register(priority=-10)
def try_publish_art(backend, artwork_id):
    art = backend.art[artwork_id]._obj
    if art.name and art.complete:
        art.approved = True


@register(priority=-100)
def remove_artifact(backend, artifact_id):
    db = backend._db
    artifact = db.query(tables.Artifact).get([artifact_id])
    db.delete(artifact)
    try:
        db.flush()
    except ValueError:  # xxx
        db.rollback()
    else:
        assert artifact.storage_type == 'scratch'
        path = os.path.join(backend._scratch_dir, artifact.storage_location)
        os.unlink(path)
