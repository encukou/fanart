<%inherit file="../base.mako" />

<p>Všechno v tomto formuláři je nepovinné.</p>
<p>To co tu vyplníš bude ukazováno veřejně (kromě data narození a e-mailu, které si můžeš nastavit). Administrátoři stránky vidí úplně všechno.</p>
<p>Nezadávej informace, které by o tvém účtu neměli vědět úplně neznámí lidé.</p>

${form|n}

<ul class="link-line user-link-line">
    <li class="action-link">${this['avatar'].link('Změnit avatar')}</li>
</ul>
