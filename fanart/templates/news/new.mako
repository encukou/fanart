<%inherit file="../base.mako" />

Přidej novou novinku na hlavní stránku!

<form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
<fieldset>
<textarea name="contents" class="markdown-textarea"></textarea>
<input type="hidden" name="csrft" value="${request.session.get_csrf_token()}"></button>
</fieldset>
<fieldset>
<button type="submit" name="submit" value="submit">Přidat</button>
</fieldset>
</form>
