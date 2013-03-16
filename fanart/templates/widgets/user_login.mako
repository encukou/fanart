<% from fanart.views.users import render_mini_login_form, render_mini_logout_form %>

<% user = this.request.user %>

<details open>
    <summary>Login</summary>
    % for message in this.request.session.pop_flash('login'):
        <div class="flash">${message}</div>
    % endfor
    % if user.is_virtual:
        <div class="login">
            ${render_mini_login_form(this) |n}
        </div>
        <div class="links">
            <a href="${request.root['users', 'new'].url}">Založit nový účet</a>
        </div>
    % else:
        <div><a href="${request.root['me'].url}">${user.name}</a></div>
        <div class="login">
            ${render_mini_logout_form(this) |n}
        </div>
        <div class="links">
            <a href="${request.root['me', 'edit'].url}">Tvůj účet</a>
        </div>
        <div class="links">
            <a href="${request.root['art', 'manage', 'upload'].url}">Přidat obrázek</a>
        </div>
    % endif
</details>
