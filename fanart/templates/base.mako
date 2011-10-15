<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>${self.title_in_head()}Česká PokéGalerie ~ Pokémon</title>
  <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
  <link rel="shortcut icon" href="${request.static_url('fanart:static/favicon.ico')}" />
  <link rel="stylesheet" href="${this.root['css'].url}" type="text/css" media="screen" charset="utf-8" />
  <!--[if lte IE 6]>
  <link rel="stylesheet" href="${request.application_url + '/css/ie6'}" type="text/css" media="screen" charset="utf-8" />
  <![endif]-->
</head>
<body class="no-js fanart">
    <div class="title" title="Česká PokéGalerie pana Smeargla ^_^"><a href="${this.root.url}">&nbsp;</a></div>
    <div class="content" id="content">
        <div class="hierarchy">
            <a href="http://pikachu.cz">Pikachu.cz</a>
            % for x in reversed(list(this.lineage)):
                » <a href="${x.url}">${x.friendly_name}</a>
            % endfor
        </div>
            ${next.body()}
    </div>
    <hr>
    <div class="usernav">
        <h2>Login</h2>
        <h2>Odkazy</h2>
        <h2>K přidání</h2>
        <h2>Shoutbox</h2>
        <h2>Odmítnuté</h2>
        <h2>Tvá práva</h2>
    </div>
    <div class="sitenav">
        <h2>Hledání</h2>
        <h2>Galerie</h2>
        <h2>Počitadlo</h2>
    </div>
    <div class="links">
        <h2>Odkazy</h2>
    </div>
</body>
</html>

<%def name="title()"></%def>
<%def name="title_in_head()">${self.title() + ' - '}</%def>
