<%def name="title()">${getattr(this, 'page_title', this.friendly_name)}</%def>
<%def name="title_in_head()">${self.title() + ' - '}</%def>
<%def name="title_in_page()"><h1>${self.title()}</h1></%def>
<%namespace name="helpers" file="helpers.mako" inheritable="True"/>

<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
  <title>${self.title_in_head()}Česká PokéGalerie ~ Pokémon</title>
  <link rel="shortcut icon" href="${request.static_url('fanart:static/favicon.png')}" />
  <link rel="stylesheet" href="${this.root['css'].url}" type="text/css" media="screen" charset="utf-8" />
  <link rel="stylesheet" href="${request.static_url('fanart:static/css/font-awesome.min.css')}" type="text/css" media="screen" charset="utf-8" />
  <link href='http://fonts.googleapis.com/css?family=Ubuntu:400,700,400italic,700italic|Gentium+Book+Basic:400,400italic,700,700italic&amp;subset=latin-ext,latin' rel='stylesheet' type='text/css'/>
  <script src="${request.static_url('fanart:static/js/jquery-1.7.1.min.js')}" type="text/javascript"></script>
  <script src="${request.static_url('fanart:static/js/jquery.details.min.js')}" type="text/javascript"></script>
  <script src="${request.static_url('fanart:static/js/jquery.timeago.js')}" type="text/javascript"></script>
  <script src="${request.static_url('fanart:static/js/script.js')}" type="text/javascript"></script>
  <script src="${request.static_url('deform:static/scripts/deform.js')}" type="text/javascript"></script>
  <!--<script src="https://browserid.org/include.js" type="text/javascript"></script>-->
  <!--[if lte IE 7]>
  <link rel="stylesheet" href="${request.static_url('fanart:static/css/font-awesome-ie7.min.css')}" type="text/css" media="screen" charset="utf-8" />
  <![endif]-->
  <!--[if lte IE 6]>
  <link rel="stylesheet" href="${request.application_url + '/css/ie6'}" type="text/css" media="screen" charset="utf-8" />
  <![endif]-->
</head>
<body class="fanart no-js wide ${'full-view' if this.fullview else ''}">
    <header>
        <div class="title" title="Česká PokéGalerie pana Smeargla ^_^"><a href="${this.root.url}">&nbsp;</a></div>
    </header>
    <section id="content">
        <nav class="hierarchy">
            <ul>
                % for x in reversed(list(this.lineage)):
                    % if x.friendly_name:
                        <li><a href="${x.url}">${x.friendly_name}</a></li>
                    % endif
                % endfor
            </ul>
        </nav>
        ${self.title_in_page()}
        ${next.body()}
    </section>
    <hr>
    <footer>
        <section id="usernav">
            <%include file="widgets/user_login.mako" />
            <%include file="widgets/art_management.mako" />
            <%include file="widgets/shoutbox.mako" />
        </section>
        <section id="sitenav">
            <%include file="widgets/userlist.mako" />
            <!--
            <details open>
                <summary>Hledání</summary>
                <form>
                    <input type="text" results="5" autosave="fanart" name="q" id="side_search">
                </form>
            </details>
            <details open>
                <summary>Galerie</summary>
            </details>
            <details>
                <summary>Počitadlo</summary>
            </details>
            -->
        </section>
        <section id="links">
            <section>
                <h2>Odkazy</h2>
                <ul class="link-line">
                    <li class="action-link">
                        <a href="http://www.pikachu.cz">pikachu.cz</a>
                    </li>
                    <li class="action-link">
                        <a href="http://www.pjz.cz">pjz.cz</a>
                    </li>
                    <li class="action-link">
                        <a href="http://isshu.cz">isshu.cz</a>
                    </li>
                </lu>
            </section>
        </section>
        <div id="helper">
            <input type="hidden" id="csrft" value="${request.csrf_token}">
            <input type="hidden" id="api_base" value="${request.root['api'].url}">
            <input type ie sucks>
        </div>
    </footer>
</body>
</html>
