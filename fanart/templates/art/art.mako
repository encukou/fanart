<%inherit file="../base.mako" />

<div>
    <img src="${request.root.url + '/scratch/' + artwork.current_version.artifacts['view'].storage_location}">
</div>
