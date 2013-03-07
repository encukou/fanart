<%inherit file="../base.mako" />

<div>Tohle je místo pro galerijní novinky; je-li tvá informace o pokémonech obecně, zkus to na <a href="http://isshu.cz">isshu.cz</a>.</div>

<form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
<fieldset>
<input type="text" name="heading" class="long-text" value="${request.POST.get('heading', '')}">
<textarea name="content" class="markdown-textarea">${request.POST.get('content', '')}</textarea>
<input type="hidden" name="csrft" value="${request.csrf_token}"></button>
</fieldset>
<fieldset>
<button type="submit" name="submit" value="submit">Přidat</button>
</fieldset>
</form>
