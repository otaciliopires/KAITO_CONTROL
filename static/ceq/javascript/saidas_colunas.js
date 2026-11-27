(() => {
'use strict';
const picker=document.getElementById('colunas-relatorio'),table=document.getElementById('tabela-saidas');
if(!picker||!table)return;
const inputs=Array.from(picker.querySelectorAll('input[name="coluna"]'));
const status=document.getElementById('colunas-status'),count=document.getElementById('colunas-contagem');
const visible=()=>inputs.filter(i=>i.checked).map(i=>i.value);
function urlColumns(anchor,ids){const url=new URL(anchor.href,location.href);url.searchParams.delete('coluna');url.searchParams.set('personalizar_colunas','1');for(const id of ids)url.searchParams.append('coluna',id);anchor.href=url.toString();}
function update(){const ids=visible(),active=new Set(ids);table.querySelectorAll('[data-coluna]').forEach(cell=>cell.hidden=!active.has(cell.dataset.coluna));table.querySelectorAll('.s-empty').forEach(cell=>cell.colSpan=ids.length);table.style.minWidth=Math.max(320,Math.min(1250,ids.length*114))+'px';count.textContent=ids.length+' de '+inputs.length+' visíveis';const pdf=document.getElementById('saidas-pdf');if(pdf)urlColumns(pdf,ids);document.querySelectorAll('.s-pagination a').forEach(a=>urlColumns(a,ids));}
for(const input of inputs)input.addEventListener('change',()=>{if(!visible().length){input.checked=true;status.textContent='Mantenha pelo menos uma coluna visível.';return;}update();status.textContent='Colunas atualizadas na tabela e no PDF.';});
document.getElementById('mostrar-todas-colunas').addEventListener('click',()=>{inputs.forEach(i=>i.checked=true);update();status.textContent='Todas as colunas estão visíveis.';});
update();
})();
