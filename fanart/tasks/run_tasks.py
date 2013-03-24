"""
from pyramid.response import Response
from sqlalchemy.orm.exc import NoResultFound
import yaml
import os
import tempfile
import contextlib
import hashlib
import shutil

from fanart.views.base import ViewBase
from fanart.models import tables

IDENTIFY_BINARY = '/usr/bin/identify'
CONVERT_BINARY = '/usr/bin/convert'
PNGCRUSH_BINARY = '/usr/bin/pngcrush'

class RunTask(ViewBase):
    def render(self, request):
        result = run_task(request)
        yaml_result = yaml.safe_dump(result)
        print(yaml_result)
        response = Response(yaml_result)
        response.content_type = 'text/plain'
        return response

def select_task(request):
    query = request.db.query(tables.ArtworkArtifact)
    query = query.filter(tables.ArtworkArtifact.type == 'scratch')
    query = query.limit(1)
    try:
        artwork_artifact = query.one()
    except NoResultFound:
        pass
    else:
        if (
                artwork_artifact.artifact.width is None or
                artwork_artifact.artifact.height is None or
                artwork_artifact.artifact.filetype is None):
            yield lambda: identify_artifact(request, artwork_artifact)
        artwork_version = artwork_artifact.artwork_version
        existing_types = artwork_version.artwork_artifacts.keys()
        for new_type in ['thumb', 'view', 'full']:
            if new_type not in existing_types:
                yield lambda: generate_artifact(
                    request, artwork_artifact, new_type)
                break
        else:
            yield lambda: remove_scratch_artifact(request, artwork_artifact)


def link_artifact(request, artifact_version, new_type):
    new_artwork_artifact = tables.ArtworkArtifact(
        artwork_version=artifact_version.artwork_version,
        artifact=artifact_version.artifact,
        type=new_type,
        )
    request.db.add(new_artwork_artifact)
    request.db.flush()
    identify_artifact(request, new_artwork_artifact)
    request.db.commit()
    return dict(
        action='link_artifact',
        new_type=new_type,
        artifact_size=(
            artifact_version.artifact.width, artifact_version.artifact.height),
        )


def generate_artifact(request, artwork_artifact, new_type):
    scratch_artifact = artwork_artifact.artifact
    orig_artwork_version = artwork_artifact.artwork_version
    assert artwork_artifact.type == 'scratch'
    path = get_scratch_path(request, artwork_artifact)
    print(artwork_artifact.artwork.id)
    comment = 'Vystaveno na poke.fanart.cz/art/{id}'.format(
        id=artwork_artifact.artwork.id)
    command_line = [
        CONVERT_BINARY,
        path,
        '-comment', comment,
        ]
    if new_type == 'thumb':
        if (artwork_artifact.artifact.width > 162 or
                artwork_artifact.artifact.height > 100):
            command_line += [
                '-resize', '162x100',
                ]
    elif new_type == 'view':
        if (scratch_artifact.width <= 162 and
                scratch_artifact.height <= 100):
            return link_artifact(
                request,
                orig_artwork_version.artwork_artifacts['thumb'], new_type)
        command_line += [
            '-resize', '500x400',
            ]
    elif new_type == 'full':
        if (scratch_artifact.width <= 500 and
                scratch_artifact.height <= 400):
            return link_artifact(
                request,
                orig_artwork_version.artwork_artifacts['view'], new_type)
    else:
        raise ValueError(new_type)
    filetype = 'png'
    with contextlib.ExitStack() as exit_stack:
        fd, converted_filename = tempfile.mkstemp(suffix='.' + filetype)
        exit_stack.callback(os.unlink, converted_filename)
        command_line.append(converted_filename)
        stdout, stderr = convert_out = run_process(command_line)
        assert not stderr, stderr
        size_converted = os.stat(converted_filename).st_size
        assert size_converted

        fd, crushed_filename = tempfile.mkstemp(suffix='.png')
        exit_stack.callback(os.unlink, crushed_filename)
        pngcrush_command_line = [
            PNGCRUSH_BINARY,
            '-bail', '-cc', '-reduce',
            '-text', 'a', 'Comment', comment,
            converted_filename,
            crushed_filename,
            ]
        stdout, stderr = crush_out = run_process(pngcrush_command_line)
        size_crushed = 0
        file_hash = hashlib.sha256()
        with open(crushed_filename, 'rb') as crushed_file:
            while True:
                data = crushed_file.read(2<<16)
                if not data:
                    break
                size_crushed += len(data)
                file_hash.update(data)
        hexdigest = file_hash.hexdigest()
        digest = file_hash.digest()
        assert size_crushed

        filename = '{}.{}'.format(hexdigest, filetype)
        path = request.fanart_settings['fanart.scratch_dir']
        path = os.path.join(path, filename)
        if not os.path.exists(path):
            shutil.move(crushed_filename, path)
            open(crushed_filename, 'w').close()
        try:
            new_artifact = tables.Artifact(
                storage_type='scratch',
                storage_location=filename,
                hash=digest,
                )
            request.db.add(new_artifact)
            request.db.flush()
            new_artwork_artifact = tables.ArtworkArtifact(
                artwork_version=orig_artwork_version,
                artifact=new_artifact,
                type=new_type,
                )
            request.db.add(new_artwork_artifact)
            request.db.flush()
            identification = identify_artifact(request, new_artwork_artifact)
            request.db.commit()
        except:
            os.unlink(crushed_filename)
            raise

    return dict(
        action='generate_artifact',
        name=artwork_artifact.artwork.name,
        new_type=new_type,
        command_line=command_line,
        size_converted=size_converted,
        size_crushed=size_crushed,
        pngcrush_command_line=pngcrush_command_line,
        convert_out=convert_out,
        crush_out=crush_out,
        hexdigest=hexdigest,
        path=path,
        identification=identification,
        )


def remove_scratch_artifact(request, artwork_artifact):
    assert artwork_artifact.type == 'scratch'
    request.db.delete(artwork_artifact)
    request.db.commit()
    return dict(
        action='remove_scratch_artifact',
        name=artwork_artifact.artwork.name,
        id=artwork_artifact.id,
        )


def run_task(request):
    for task in select_task(request):
        return task()
"""