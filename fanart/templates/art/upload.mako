<%inherit file="../base.mako" />

<form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
<fieldset>
<div>Jméno obrázku</div>
<input type="text" name="title" class="long-text" value="${request.POST.get('title', '')}">
<div>Soubor</div>
<input type="file" name="image" value="Vybrat obrázek" />
<input type="hidden" name="csrft" value="${request.csrf_token}"></button>
</fieldset>
<fieldset>
<button type="submit" name="submit" value="submit">Nahrát</button>
</fieldset>
</form>

<hr>

<div>
    Po nahrání obrázku se k němu musí vytvořit náhled. Měj prosím trpělivost.
</div>
<div>
    Maximální velikost obrázku je cca 1,5 MB.
</div>
<div>
    Máš-li s přidáváním problémy (například: chceš poslat video či hudbu,
    nemáš skener/foťák, obrázek je příliš velký), napiš e-mail
    na <a href="mailto:encukou@gmail.com">encukou@gmail.com</a>.
</div>
<div>
    Tvůj obrázek bude změněn (zmenšen, okomentován, atd.), a tato stránka
    nenese žádnou odpovědnost za obrázky na ní vystavené. Vždycky si od svého
    obrázku nechávej kopii u sebe!
</div>
<div>
    Tvůrci Fanartu si vyhrazují právo nahrané obrázky šířit
    a vystavovat, samozřejmě vždy s uvedením autora.
</div>
