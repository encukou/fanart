import os
import subprocess
import contextlib
import shutil
import hashlib
import tempfile

from fanart.models import tables

IDENTIFY_BINARY = '/usr/bin/identify'
CONVERT_BINARY = '/usr/bin/convert'

def run_process(command_line):
    process = subprocess.Popen(
        command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command_line)
    return stdout, stderr


def identify_artifact(backend, artifact):
    # XXX: Non-images!
    if artifact.storage_type != 'scratch':
        print('Artifact {} not in scratch'.format(artifact.id))
        return False
    if artifact.filetype:
        print('Artifact {} already identified'.format(artifact.id))
        return
    path = os.path.join(backend._scratch_dir, artifact.storage_location)
    command_line = [
        IDENTIFY_BINARY,
        '-format', '%m;%w;%h;',
        path,
        ]
    try:
        stdout, stderr = run_process(command_line)
    except subprocess.CalledProcessError:
        artifact.error_message = 'Neznámý formát obrázku'
        print('Artifact {}: Identify failed'.format(artifact.id))
        return False
    stdout = stdout.decode('utf-8')
    filetype, width, height, extra = stdout.split(';', 3)
    extra = extra.strip()
    if filetype == 'GIF' and 'GIF' in extra:
        filetype = 'Animated GIF'
    elif extra:
        artifact.error_message = 'Nepodporovaná animace'
        print('Artifact {}: Bad animation'.format(artifact.id))
        return False
    elif filetype == 'JPEG':
        filetype = 'JPEG'
    elif filetype == 'PNG':
        filetype = 'PNG'
    else:
        filetype = 'Image'
    artifact.filetype = filetype = filetype.strip()
    artifact.width = width = int(width.strip())
    artifact.height = height = int(height.strip())
    return True


def resize_image(backend, artifact, filetype, max_width=None, max_height=None,
                 comment=None):
    identify_artifact(backend, artifact)
    if artifact.storage_type != 'scratch':
        print('Artifact {} storage type is {} - cannot resize'.format(
            artifact.id, artifact.storage_type))
        return
    if artifact.error_message:
        print('Artifact {} has error - cannot resize'.format(artifact.id))
        return
    path = os.path.join(backend._scratch_dir, artifact.storage_location)
    command_line = [CONVERT_BINARY]
    if comment:
        command_line += ['-comment', comment]
    command_line += [path]
    if (max_width and artifact.width > max_width) or (
            max_height and artifact.height > max_height):
        command_line += ['-resize', '{}x{}'.format(max_width, max_height)]
    if filetype != 'gif':
        command_line += ['-background', 'transparent', '-flatten']
    suffix = '.' + filetype
    fd, converted_filename = tempfile.mkstemp(suffix=suffix)
    with contextlib.ExitStack() as exit_stack:
        exit_stack.callback(os.unlink, converted_filename)
        command_line.append(converted_filename)
        stdout, stderr = run_process(command_line)
        assert not stderr, stderr
        size_converted = os.stat(converted_filename).st_size
        assert size_converted

        size = 0
        file_hash = hashlib.sha256()
        with open(converted_filename, 'rb') as crushed_file:
            while True:
                data = crushed_file.read(2<<16)
                if not data:
                    break
                size += len(data)
                file_hash.update(data)
        hexdigest = file_hash.hexdigest()
        digest = file_hash.digest()
        assert size

        filename = '{}.{}'.format(hexdigest, filetype)
        path = os.path.join(backend._scratch_dir, filename)
        if not os.path.exists(path):
            shutil.move(converted_filename, path)
            open(converted_filename, 'w').close()
        new_artifact = tables.Artifact(
            storage_type='scratch',
            storage_location=filename,
            hash=digest,
            )
        backend._db.add(new_artifact)
        backend._db.flush()
        identify_artifact(backend, new_artifact)
        return new_artifact


def process_image(backend, artwork_version, scratch_artifact, size,
                 artifact_type, base=None, keep_animations=False):
    identify_artifact(backend, scratch_artifact)
    artwork_id = artwork_version.artwork_id
    comment = 'vystaveno na poke.fanart.cz/art/{}'.format(artwork_id)
    animated = False
    if scratch_artifact.filetype == 'JPEG':
        filetype = 'jpeg'
    elif scratch_artifact.filetype == 'Animated GIF':
        if keep_animations:
            filetype = 'gif'
            animated = True
        else:
            filetype = 'png'
    elif scratch_artifact.filetype in ('Image', 'PNG', ):
        filetype = 'png'
    else:
        raise ValueError('Unknown filetype %s' % scratch_artifact.filetype)
    if base and not animated:
        base_artifact, (width, height) = base
        if (scratch_artifact.width <= width and
                scratch_artifact.height <= height):
            print('Reusing base')
            artwork_version.artifacts[artifact_type] = base_artifact
            backend._db.flush()
            return
    if not size:
        size = ()
    else:
        width, height = size
    new_artifact = resize_image(
        backend, scratch_artifact, filetype, *size, comment=comment)
    artwork_version.artifacts[artifact_type] = new_artifact
    backend._db.flush()
