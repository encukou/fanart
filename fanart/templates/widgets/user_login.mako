<% from fanart.views.users import render_mini_login_form, render_mini_logout_form %>

<% user = this.request.session.user %>
% if not user.logged_in:
<details open>
    <summary>Login</summary>
    <div class="login">
        ${render_mini_login_form(this) |n}
    </div>
    <div class="links">
        <a href="${request.root['users', 'new'].url}">Založit nový účet</a>
    </div>
</details>
% else:
<details open>
    <summary>Login</summary>
    <div>${user.name}</div>
    <div class="login">
        ${render_mini_logout_form(this) |n}
    </div>
    <div class="links">
        <a href="${request.root['me', 'edit'].url}">Tvůj účet</a>
    </div>
</details>
% endif
